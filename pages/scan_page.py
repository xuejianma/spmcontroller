import numpy as np
from util.plotscanrange import update_graphs

def determine_scan_window(self):
        self.piezo_limit_x = self.doubleSpinBox_piezo_limit_x.value()
        self.piezo_limit_y = self.doubleSpinBox_piezo_limit_y.value()
        self.xmin_input = self.doubleSpinBox_x_min.value()
        self.xmax_input = self.doubleSpinBox_x_max.value()
        self.ymin_input = self.doubleSpinBox_y_min.value()
        self.ymax_input = self.doubleSpinBox_y_max.value()
        self.xpixels = self.spinBox_x_pixels.value()
        self.ypixels = self.spinBox_y_pixels.value()
        self.frequency = self.doubleSpinBox_frequency.value()
        self.rotation_degree = self.doubleSpinBox_rotation.value()
        self.rotation = self.rotation_degree / 180 * np.pi
        center = np.array([[(self.xmin_input + self.xmax_input) / 2,
                                (self.ymin_input + self.ymax_input) / 2]]).T
        p1_input = np.array([self.xmin_input, self.ymin_input])
        p2_input = np.array([self.xmax_input, self.ymin_input])
        p3_input = np.array([self.xmax_input, self.ymax_input])
        p4_input = np.array([self.xmin_input, self.ymax_input])
        rotate_matrix = np.array([[np.cos(self.rotation), -np.sin(self.rotation)],
                                        [np.sin(self.rotation), np.cos(self.rotation)]])
        self.p1 = rotate_coord(p1_input, center, rotate_matrix)
        self.p2 = rotate_coord(p2_input, center, rotate_matrix)
        self.p3 = rotate_coord(p3_input, center, rotate_matrix)
        self.p4 = rotate_coord(p4_input, center, rotate_matrix)

        self.X_raw = np.round(np.linspace(0, self.xmax_input - self.xmin_input, self.xpixels), 6)
        self.Y_raw = np.round(np.linspace(0, self.ymax_input - self.ymin_input, self.ypixels), 6)
        XX_input, YY_input = np.meshgrid(self.X_raw + self.xmin_input, self.Y_raw + self.ymin_input)
        xx_yy = np.array([np.array([xx, yy]) for xx, yy in zip(XX_input.reshape((1, -1)), YY_input.reshape((1, -1)))])
        xx_yy_rot = rotate_coord(xx_yy, center, rotate_matrix)
        self.XX = xx_yy_rot[0, :].reshape(XX_input.shape)
        self.YY = xx_yy_rot[1, :].reshape(YY_input.shape)
        update_graphs(self)


def rotate_coord(p, center, rotate_matrix):
        p = np.reshape(p, (2, -1))
        if p.shape[1] == 1:
                return np.round(np.reshape(np.matmul(rotate_matrix, (p - center)) + center, (-1, 2))[0], 6)
        else:
                return np.round(np.reshape(np.matmul(rotate_matrix, (p - center)) + center, (2, -1)), 6)