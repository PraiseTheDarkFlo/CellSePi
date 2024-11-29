from matplotlib import pyplot as plt

from data_util import load_image_to_numpy
import scipy.signal as sig
import scipy.ndimage as ndimg
import numpy as np

conv_size = 9
horz_filt = np.zeros((conv_size, conv_size))
horz_filt[int(conv_size / 2), :] = 1
vert_filt = np.rot90(horz_filt)

if __name__ == '__main__':
    path = "/Users/erik/Documents/Promotion/Projekte/Anjas_Stuff/_data/Segmentation Training Data/28-06-2024/output/Series003c4.tif"
    image = load_image_to_numpy(path)

    #    image *= 5
    threshold = np.quantile(image, q=0.9)
    print(f"Threshold: {threshold}")
    # filtered_image = (image >= threshold) * 1
    filtered_image = np.array(image)
    filtered_image[image < threshold] = 0
    thresholded_image = filtered_image
    #
    # filtered_image = ndimg.gaussian_filter(filtered_image, sigma=1)
    filtered_image = ndimg.median_filter(filtered_image, size=3)
    filtered_image = ndimg.convolve(filtered_image, np.rot90(np.eye(conv_size))) \
                     + ndimg.convolve(filtered_image, np.eye(conv_size)) \
                     + ndimg.convolve(filtered_image, horz_filt) \
                     + ndimg.convolve(filtered_image, vert_filt)
    filtered_image = ndimg.median_filter(filtered_image, size=3)
    # filtered_image *= 0.25

    gaussian_filtered_image = filtered_image

    filtered_image = (filtered_image > np.quantile(filtered_image, 0.9))
    filtered_image = ndimg.convolve(filtered_image, np.rot90(np.eye(conv_size))) \
                     + ndimg.convolve(filtered_image, np.eye(conv_size)) \
                     + ndimg.convolve(filtered_image, horz_filt) \
                     + ndimg.convolve(filtered_image, vert_filt)
    filtered_image = ndimg.median_filter(filtered_image, size=3)

    convolution_filtered_image = filtered_image

    # filtered_image = ndimg.percentile_filter(filtered_image, percentile=0.5, size=3)
    # percentile_filtered_image = filtered_image

    # filtered_image = ndimg.maximum_filter(filtered_image, size=3)

    for iQ in range(0):
        cur_t = np.quantile(filtered_image, q=0.9)
        if iQ > 0:
            cur_t = 2
        print(f"Threshold: {cur_t}")
        filtered_image = ndimg.gaussian_filter(filtered_image, sigma=1, truncate=5)
        # filtered_image = ndimg.percentile_filter(filtered_image, 0.9, size=3)
        filtered_image = (filtered_image >= cur_t) * 10

    percentile_filtered_image = filtered_image

    # # median_filtered_image = sig.medfilt2d(thresholded_image, kernel_size=3)
    # filtered_image = ndimg.maximum_filter(filtered_image, size=3)
    # max_filtered_image = filtered_image
    # # thresholded_image = (max_filtered_image >= threshold) * 1
    #
    # filtered_image = ndimg.gaussian_filter(filtered_image, sigma=1)
    # gaussian_filtered_image = filtered_image
    # filtered_image = (filtered_image >= 1.5*np.median(filtered_image)) * 1
    # # filtered_image = sig.medfilt2d(filtered_image, kernel_size=3)
    # # filtered_image = filtered_image

    # median_filtered_image2 = sig.medfilt2d(median_filtered_image, kernel_size=5)
    # median_filtered_image2 = sig.medfilt2d(median_filtered_image2, kernel_size=5)
    filtered_image = filtered_image / np.max(filtered_image)
    border_width = 5
    pre_labeling_image = 1 - filtered_image
    # pre_labeling_image[:, 0:border_width] = 0
    # pre_labeling_image[:, -border_width:] = 0
    # pre_labeling_image[0:border_width, :] = 0
    # pre_labeling_image[-border_width:, :] = 0
    # pre_labeling_image = np.rot90(pre_labeling_image)
    # pre_labeling_image = pre_labeling_image[:256, :256]
    labeled_image = ndimg.label(pre_labeling_image)[0]

    fig, axes = plt.subplots(2, 2, sharex=True, sharey=True)
    ax = axes[0, 0]
    ax.imshow(image)

    ax = axes[0, 1]
    ax.imshow(thresholded_image)

    ax = axes[1, 0]
    ax.imshow(pre_labeling_image)
    # ax.imshow(gaussian_filtered_image)

    ax = axes[1, 1]
    # ax.imshow(percentile_filtered_image)
    ax.imshow(labeled_image, cmap="gist_rainbow")

    plt.show()

    pass
