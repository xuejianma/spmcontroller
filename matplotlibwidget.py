#
#
# from matplotlib.figure import Figure
# from matplotlib.backends.backend_qt5agg import FigureCanvas
#
#
# class MatplotlibWidget(FigureCanvas):
#     def __init__(self, parent=None):
#         super(MatplotlibWidget, self).__init__(Figure())
#         self.setParent(parent)
#         self.figure.tight_layout(pad=0)
#         self.plot_content = None
#
#
#     def plot2D(self, X, Y, array2D):
#         # self.plot_content =
#         self.plot_content.clear()
#         self.plot_content = self.figure.add_subplot(111, position=[0, 0, 1, 1])
#         # self.plot_content.axis("off")
#         self.plot_content.use_sticky_edges = True
#         self.plot_content.set_title(None)
#         self.plot_content.invert_xaxis()
#         self.plot_content.invert_yaxis()
#         self.plot_content.set_xlabel(None)
#         self.plot_content.set_ylabel(None)
#         self.plot_content.margins(0)
#         self.figure.subplots_adjust(
#             left=0, right=1, top=1, bottom=0, wspace=0, hspace=0
#         )
#         self.figure.tight_layout(pad=0)
#         self.plot_content.pcolormesh(X, Y, array2D, cmap = 'afmhot')
#         self.draw()
