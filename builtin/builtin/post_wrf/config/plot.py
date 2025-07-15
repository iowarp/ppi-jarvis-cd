import argparse
import adios2                               # pylint: disable=import-error
import numpy as np                          # pylint: disable=import-error
import matplotlib.pyplot as plt             # pylint: disable=import-error
import matplotlib.gridspec as gridspec      # pylint: disable=import-error
from mpi4py import MPI                      # pylint: disable=import-error
import cartopy.crs as ccrs                  # pylint: disable=import-error
import cartopy.feature as cfeature          # pylint: disable=import-error
from mpl_toolkits.axes_grid1 import make_axes_locatable # pylint: disable=import-error
#
#
def setup_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--instream", "-i", help="Name of the input stream", default="wrfout_d01_2019-11-26_23:00:00")
    parser.add_argument("--outfile", "-o", help="Name of the output file", default="screen")
    parser.add_argument("--varname", "-v", help="Name of variable read", default="T2")
    args = parser.parse_args()
    return args

def plot_var(var, fr_step):

    lccproj = ccrs.LambertConformal(central_longitude=-74.5, central_latitude=38.8)
    fig, ax = plt.subplots(figsize=(15, 18), subplot_kw=dict(projection=lccproj))
    plt.subplots_adjust(right=0.88)  # adjust the right margin of the plot
    title = fr_step.read_string("Times")
    plt.title("WRF-ADIOS2 Demo \n {}".format(title[0]), fontsize=17)

     # format the spacing of the colorbar
    divider = make_axes_locatable(ax)
    cax = divider.new_horizontal(size='5%', pad=0.1, axes_class=plt.Axes)
    fig.add_axes(cax)

    displaysec = 0.5
    cur_step = fr_step.current_step()
    x = fr_step.read("XLONG")
    y = fr_step.read("XLAT")
    data = fr_step.read(var)
    print(data)
    data = data * 9 / 5 - 459.67 #convert from K to F

    # define the limits for the model to subset and plot
    # model_lims = dict(minlon=-80, maxlon=-69, minlat=35, maxlat=43)

    # # create boolean indices where lat/lon are within defined boundaries
    # lon_ind = np.logical_and(x > model_lims['minlon'], x < model_lims['maxlon'])
    # lat_ind = np.logical_and(y > model_lims['minlat'], y < model_lims['maxlat'])
    # # find i and j indices of lon/lat in boundaries
    # ind = np.where(np.logical_and(lon_ind, lat_ind))

    # data = np.squeeze(data)[range(np.min(ind[0]), np.max(ind[0]) + 1),
    #                 range(np.min(ind[1]), np.max(ind[1]) + 1)]

    h = ax.pcolormesh(x, y, data, vmin=-20, vmax=110,
                      cmap='jet', transform=ccrs.PlateCarree())

    cb = plt.colorbar(h, cax=cax)
    cb.set_label(label="Temperature [F]", fontsize=14)  # add the label on the colorbar
    cb.ax.tick_params(labelsize=12)  # format the size of the tick labels

    # add contours
    contour_list = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # define contour levels
    cs = ax.contour(x, y, data, contour_list, colors='black',
                    linewidths=.5, transform=ccrs.PlateCarree())
    ax.clabel(cs, inline=True, fontsize=10.5, fmt='%d')

    # add the latitude and longitude gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=1, color='gray', alpha=0.5,
                      linestyle='dotted', x_inline=False)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 13}
    gl.ylabel_style = {'size': 13}

     # add map features
    land = cfeature.NaturalEarthFeature('physical', 'land', '10m')
    ax.add_feature(land, zorder=5, edgecolor='black', facecolor='none')

    state_lines = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='10m',
        facecolor='none')

    ax.add_feature(cfeature.BORDERS, zorder=6)
    ax.add_feature(state_lines, zorder=7, edgecolor='black')

    #plt.title(title)

    # plt.ion()
    #plt.show()
    # plt.pause(displaysec)
    # #clear_output()
    # plt.clf()

    imgfile = "image"+"{0:0>5}.png".format(cur_step)
    plt.savefig(imgfile)
    plt.clf()

if __name__ == "__main__":
    args = setup_args()
    fr = adios2.open(args.instream, "r", MPI.COMM_WORLD, "adios2.xml", "wrfout_d01_2019-11-26_23:00:00")

    for fr_step in fr:
        plot_var(args.varname, fr_step)

    fr.close()
