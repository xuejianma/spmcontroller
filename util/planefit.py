"""
Created by Xuejian Ma at 12/20/2021.
All rights reserved.
"""
import numpy as np
from scipy.optimize import curve_fit


class PlaneFit:
    def __init__(self):
        self.p1 = 0
        self.p2 = 0

    def func(self, X, a, b):
        x, y = X
        return a * x + b * y

    def fit(self, points):
        points = np.asarray(points)
        if np.shape(points)[0] <= 2:
            self.p1 = 0
            self.p2 = 0
            print("At least 3 points should be selected for plane fitting.")
        else:
            X = points[:, 0]
            Y = points[:, 1]
            Z = points[:, 2]
            P0 = 0., 0.  # initial guess
            (self.p1, self.p2), cov = curve_fit(self.func, (X, Y), Z, P0)
        print(self.p1, self.p2)

    def get_delta_z_plane_fitted(self, x, y):
        return np.round(self.func((x, y), self.p1, self.p2), 6)
