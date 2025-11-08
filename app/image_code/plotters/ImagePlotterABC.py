from abc import ABC, abstractmethod


class ImagePlotterABC(ABC):

    def __init__(self, image):
        self.image = image

    @abstractmethod
    def plot(self):
        pass

