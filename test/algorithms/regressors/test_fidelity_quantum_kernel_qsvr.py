# This code is part of a Qiskit project.
#
# (C) Copyright IBM 2021, 2024.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Test QSVR on fidelity quantum kernel."""

import os
import tempfile
import unittest

from test import QiskitMachineLearningTestCase

import numpy as np
from sklearn.metrics import mean_squared_error

from qiskit.circuit.library import ZZFeatureMap
from qiskit_machine_learning.utils import algorithm_globals
from qiskit_machine_learning.algorithms import QSVR, SerializableModelMixin
from qiskit_machine_learning.exceptions import QiskitMachineLearningWarning
from qiskit_machine_learning.kernels import FidelityQuantumKernel

from qiskit.primitives import Sampler


class TestQSVR(QiskitMachineLearningTestCase):
    """Test QSVR Algorithm on fidelity quantum kernel."""

    def setUp(self):
        super().setUp()

        algorithm_globals.random_seed = 10598

        self.sampler = Sampler()
        self.feature_map = ZZFeatureMap(feature_dimension=2, reps=2)

        X_train = np.asarray(
            [
                [-0.36572221,  0.90579879],
                [-0.41816432,  0.03011426],
                [-0.48806982,  0.87208714],
                [-0.67078436, -0.91017876],
                [-0.12980588,  0.98475113],
                [ 0.78335453,  0.49721604],
                [ 0.78158498,  0.78689328],
                [ 0.03771672, -0.3681419 ],
                [ 0.54402486,  0.32332253],
                [-0.25268454, -0.81106666]
            ]
        )
        y_train = np.asarray([ 0.07045477,  0.80047778,  0.04493319, -0.30427998, -0.02430856,
        0.17224315, -0.26474769,  0.83097582,  0.60943777,  0.31577759])

        X_test = np.asarray(
            [
                [-0.60713067, -0.37935265],
                [ 0.55480968,  0.94365285],
                [ 0.00148237, -0.71220499],
                [-0.97212742, -0.54068794]
            ]
        )
        y_test = np.asarray([ 0.45066614, -0.18052862,  0.4549451 , -0.23674218])

        self.sample_train = X_train
        self.label_train = y_train

        self.sample_test = X_test
        self.label_test = y_test

    def test_qsvr(self):
        """Test QSVR"""
        qkernel = FidelityQuantumKernel(feature_map=self.feature_map)

        qsvr = QSVR(quantum_kernel=qkernel)
        qsvr.fit(self.sample_train, self.label_train)
        # score = qsvr.score(self.sample_test, self.label_test)

        # self.assertAlmostEqual(score, 0.38, places=2)
        predictions = qsvr.predict(self.sample_test)
        mse = mean_squared_error(self.label_test, predictions)
        self.assertAlmostEqual(mse, 0.04964456790383482, places = 4)

    def test_change_kernel(self):
        """Test QSVR with QuantumKernel later"""
        qkernel = FidelityQuantumKernel(feature_map=self.feature_map)

        qsvr = QSVR()
        qsvr.quantum_kernel = qkernel
        qsvr.fit(self.sample_train, self.label_train)
        # score = qsvr.score(self.sample_test, self.label_test)

        # self.assertAlmostEqual(score, 0.38, places=2)
        predictions = qsvr.predict(self.sample_test)
        mse = mean_squared_error(self.label_test, predictions)
        self.assertAlmostEqual(mse, 0.04964456790383482, places = 4)

    def test_qsvr_parameters(self):
        """Test QSVR with extra constructor parameters"""
        qkernel = FidelityQuantumKernel(feature_map=self.feature_map)

        qsvr = QSVR(quantum_kernel=qkernel, tol=1e-3, C=1.0)
        qsvr.fit(self.sample_train, self.label_train)
        # score = qsvr.score(self.sample_test, self.label_test)

        # self.assertAlmostEqual(score, 0.38, places=2)
        predictions = qsvr.predict(self.sample_test)
        mse = mean_squared_error(self.label_test, predictions)
        self.assertAlmostEqual(mse, 0.04964456790383482, places = 4)

    def test_qsvc_to_string(self):
        """Test QSVR print works when no *args passed in"""
        qsvr = QSVR()
        _ = str(qsvr)

    def test_with_kernel_parameter(self):
        """Test QSVC with the `kernel` argument."""
        with self.assertWarns(QiskitMachineLearningWarning):
            QSVR(kernel=1)

    def test_save_load(self):
        """Tests save and load models."""
        features = np.array([[0, 0], [0.1, 0.1], [0.4, 0.4], [1, 1]])
        labels = np.array([0, 0.1, 0.4, 1])

        quantum_kernel = FidelityQuantumKernel(feature_map=ZZFeatureMap(2))
        regressor = QSVR(quantum_kernel=quantum_kernel)
        regressor.fit(features, labels)

        # predicted labels from the newly trained model
        test_features = np.array([[0.5, 0.5]])
        original_predicts = regressor.predict(test_features)

        # save/load, change the quantum instance and check if predicted values are the same
        with tempfile.TemporaryDirectory() as dir_name:
            file_name = os.path.join(dir_name, "qsvr.model")
            regressor.save(file_name)

            regressor_load = QSVR.load(file_name)
            loaded_model_predicts = regressor_load.predict(test_features)

            np.testing.assert_array_almost_equal(original_predicts, loaded_model_predicts)

            # test loading warning
            class FakeModel(SerializableModelMixin):
                """Fake model class for test purposes."""

                pass

            with self.assertRaises(TypeError):
                FakeModel.load(file_name)


if __name__ == "__main__":
    unittest.main()
