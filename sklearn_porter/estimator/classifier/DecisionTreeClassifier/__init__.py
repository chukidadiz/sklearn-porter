# -*- coding: utf-8 -*-

from sklearn_porter.estimator.classifier.Classifier import Classifier


class DecisionTreeClassifier(Classifier):
    """
    See also
    --------
    sklearn.tree.DecisionTreeClassifier

    http://scikit-learn.org/0.18/modules/generated/sklearn.tree.DecisionTreeClassifier.html
    """

    SUPPORTED_METHODS = ['predict']

    # @formatter:off
    TEMPLATES = {
        'c': {
            'if':       'if (atts[{0}] {1} {2}) {{',
            'else':     '} else {',
            'endif':    '}',
            'arr':      'classes[{0}] = {1}',
            'indent':   '    ',
            'join':     '; ',
        },
        'go': {
            'if':       'if atts[{0}] {1} {2} {{',
            'else':     '} else {',
            'endif':    '}',
            'arr':      'classes[{0}] = {1}',
            'indent':   '\t',
            'join':     '',
        },
        'java': {
            'if':       'if (atts[{0}] {1} {2}) {{',
            'else':     '} else {',
            'endif':    '}',
            'arr':      'classes[{0}] = {1}',
            'indent':   '    ',
            'join':     '; ',
        },
        'js': {
            'if':       'if (atts[{0}] {1} {2}) {{',
            'else':     '} else {',
            'endif':    '}',
            'arr':      'classes[{0}] = {1}',
            'indent':   '    ',
            'join':     '; ',
        },
        'php': {
            'if':       'if ($atts[{0}] {1} {2}) {{',
            'else':     '} else {',
            'endif':    '}',
            'arr':      '$classes[{0}] = {1}',
            'indent':   '    ',
            'join':     '; ',
        },
        'ruby': {
            'if':       'if atts[{0}] {1} {2}',
            'else':     'else',
            'endif':    'end',
            'arr':      'classes[{0}] = {1}',
            'indent':   '    ',
            'join':     ' ',
        }
    }
    # @formatter:on

    def __init__(self, estimator, target_language='java',
                 target_method='predict', **kwargs):
        """
        Port a trained estimator to the syntax of a chosen programming language.

        Parameters
        ----------
        :param estimator : AdaBoostClassifier
            An instance of a trained DecisionTreeClassifier estimator.
        :param target_language : string
            The target programming language.
        :param target_method : string
            The target method of the estimator.
        """
        super(DecisionTreeClassifier, self).__init__(
            estimator, target_language=target_language,
            target_method=target_method, **kwargs)
        self.estimator = estimator
        self.n_features = estimator.n_features_
        self.n_classes = estimator.n_classes_

    def export(self, class_name="Brain", method_name="predict", use_repr=True):
        """
        Port a trained estimator to the syntax of a chosen programming language.

        Parameters
        ----------
        :param class_name: string, default: 'Brain'
            The name of the class in the returned result.
        :param method_name: string, default: 'predict'
            The name of the method in the returned result.
        :param use_repr : bool, default True
            Whether to use repr() for floating-point values or not.

        Returns
        -------
        :return : string
            The transpiled algorithm with the defined placeholders.
        """
        self.class_name = class_name
        self.method_name = method_name
        self.use_repr = use_repr

        if self.target_method == 'predict':
            return self.predict(class_name, method_name)

    def predict(self, class_name, method_name):
        """
        Transpile the predict method.

        Returns
        -------
        :return : string
            The transpiled predict method as string.
        """
        method = self.create_method(class_name, method_name)
        return self.create_class(method, class_name, method_name)

    def create_branches(self, left_nodes, right_nodes, threshold,
                        value, features, node, depth):
        """
        Parse and port a single tree estimator.

        Parameters
        ----------
        :param left_nodes : object
            The left children node.
        :param right_nodes : object
            The left children node.
        :param threshold : object
            The decision threshold.
        :param value : object
            The label or class.
        :param features : object
            The feature values.
        :param node : int
            The current node.
        :param depth : int
            The tree depth.

        Returns
        -------
        :return : string
            The ported single tree as function or method.
        """
        out = ''
        # ind = '\n' + '    ' * depth
        if threshold[node] != -2.:
            out += '\n'
            temp = self.temp('if', n_indents=depth)
            out += temp.format(features[node], '<=', self.repr(threshold[node]))
            if left_nodes[node] != -1.:
                out += self.create_branches(
                    left_nodes, right_nodes, threshold, value,
                    features, left_nodes[node], depth + 1)
            out += '\n'
            out += self.temp('else', n_indents=depth)
            if right_nodes[node] != -1.:
                out += self.create_branches(
                    left_nodes, right_nodes, threshold, value,
                    features, right_nodes[node], depth + 1)
            out += '\n'
            out += self.temp('endif', n_indents=depth)
        else:
            clazzes = []
            temp = self.temp('arr', n_indents=depth)
            for i, rate in enumerate(value[node][0]):
                clazz = temp.format(i, int(rate))
                clazz = '\n' + clazz
                clazzes.append(clazz)
            out += self.temp('join').join(clazzes) + self.temp('join')
        return out

    def create_tree(self):
        """
        Parse and build the tree branches.

        Returns
        -------
        :return out : string
            The tree branches as string.
        """
        feature_indices = []
        for i in self.estimator.tree_.feature:
            n_features = self.n_features
            if self.n_features > 1 or (self.n_features == 1 and i >= 0):
                feature_indices.append([str(j) for j in range(n_features)][i])

        indentation = 1 if self.target_language in ['java', 'js', 'php', 'ruby'] else 0
        return self.create_branches(
            self.estimator.tree_.children_left,
            self.estimator.tree_.children_right,
            self.estimator.tree_.threshold,
            self.estimator.tree_.value,
            feature_indices, 0, indentation)

    def create_method(self, class_name, method_name):
        """
        Build the estimator method or function.

        Returns
        -------
        :return out : string
            The built method as string.
        """
        n_indents = 1 if self.target_language in ['java', 'js', 'php', 'ruby'] else 0
        branches = self.indent(self.create_tree(), n_indents=1)
        temp_method = self.temp('method', n_indents=n_indents, skipping=True)
        out = temp_method.format(class_name=class_name, method_name=method_name,
                                 n_features=self.n_features,
                                 n_classes=self.n_classes, branches=branches)
        return out

    def create_class(self, method, class_name, method_name):
        """
        Build the estimator class.

        Returns
        -------
        :return out : string
            The built class as string.
        """
        temp_class = self.temp('class')
        out = temp_class.format(class_name=class_name, method_name=method_name,
                                method=method, n_features=self.n_features)
        return out
