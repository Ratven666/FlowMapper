from matplotlib import pyplot as plt

from app.image_code.plotters.ImagePlotterABC import ImagePlotterABC


class MPLImagePlotter(ImagePlotterABC):

    def __init__(self, image, band=1, cmap='viridis', figsize=(10, 8)):
        super().__init__(image)
        self.band = band
        self.cmap = cmap
        self.figsize = figsize

    def plot(self):
        plt.figure(figsize=self.figsize)
        plt.imshow(self.image.data[self.band - 1], cmap=self.cmap)
        plt.colorbar()
        plt.title(f'Band {self.band} | CRS: {self.image.crs}')
        plt.show()
