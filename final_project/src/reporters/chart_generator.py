import matplotlib.pyplot as plt
import os

class ChartGenerator:
    def __init__(self, outputDir="reports/charts"):
        os.makedirs(outputDir, exist_ok=True)
        self.outputDir = outputDir

    def bar_chart(self, data, labels, title, filename):
        plt.figure()
        plt.bar(labels, data)
        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        path = os.path.join(self.outputDir, filename)
        plt.savefig(path)
        plt.close()
        return path

