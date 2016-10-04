from matplotlib import animation


def vis_story_3d(story_list):
    """visualize a story list. """
    
    xvals = []
    yvals = []
    zvals = []
    vxs = []
    vys = []
    vzs = []
    masses = []
    
    for story in story_list:
        partlist = extract_particle_dynamics(story)
        
    for particle in partlist:
        xvals.append(particle[0])
        yvals.append(particle[1])
        zvals.append(particle[2])
        vxs.append(particle[3])
        vys.append(particle[4])
        vzs.append(particle[5])
        masses.append(particle[6])
        
    # now do the plot
    fig = plt.figure(figsize=(10,10))
    ax = fig.gca(projection='3d')
    ax.plot(np.array(xvals), np.array(yvals), np.array(zvals), ".")


def animate_run(therun):
    theuuid = therun.uuid
    moviename = animate_from_fs(str(theuuid), therun.nframes, use_warehouse=True)
    return moviename


def animate_panel_old(pan, prng=10.0, filebase='basic_animation'):
    """Turn a panel of star cluster evolution snapshots into a 3d animation.

    Arguments are:
    pan: the panel
    prng: plot range for all three axes.
    filebase: the base name of the file for the animation.

    returns:
    Nothing."""
    
    fig = plt.figure(figsize=(10,10))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax = fig.gca(projection='3d')
    ax.set_autoscale_on(False)
    
    nframes = pan.shape[1]
    starfield, = ax.plot([], [], [],'bo', ms=7)
    ax.set_xlim3d(-prng, prng)
    ax.set_ylim3d(-prng, prng)
    ax.set_zlim3d(-prng, prng)

    def init():
        """initialize animation"""
        starfield.set_data([], [])
        starfield.set_3d_properties(zs=[])
        return starfield
    
    def doframe(n):
        xvals = []
        yvals = []
        zvals = []
        masses = []
        
        for starid in pan.keys():
            xvals.append(pan[starid]['r'][n][0])
            yvals.append(pan[starid]['r'][n][1])
            zvals.append(pan[starid]['r'][n][2])
            masses.append(pan[starid]['m'][n])
    # not super happy with the colors yet.
        starfield.set_data(np.array(xvals), np.array(yvals))
        starfield.set_3d_properties(zs=np.array(zvals))
        return starfield

    anim = animation.FuncAnimation(fig, doframe,
                               frames=nframes, interval=20, blit=True)
    anim.save("%s.mp4"%filebase, fps=30)
    #ax.plot(np.array(xvals), np.array(yvals), np.array(zvals), ".")


def animate_from_fs(filebase, nframes, prng=10.0, use_warehouse=True):
    import pylab as plt
    from mpl_toolkits.mplot3d import axes3d
    fig = plt.figure(figsize=(10,10))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax = fig.gca(projection='3d')
    ax.set_autoscale_on(False)

    mcomfield, = ax.plot([], [], [],'go', ms=7)
    ax.set_xlim3d(-prng, prng)
    ax.set_ylim3d(-prng, prng)
    ax.set_zlim3d(-prng, prng)

    def init():
        """initialize animation"""
        mcomfield.set_data([], [])
        mcomfield.set_3d_properties(zs=[])
        return (mcomfield)
    
    def doframe(n):
        xvals = []
        yvals = []
        zvals = []
        masses = []
        
        if use_warehouse:
            xmlname = warehousepath + filebase + ".%d.xml"% n
        else:
            xmlname = filebase + ".%d.xml"% n
            
        dataframe, time, nparticles = process_frame(xmlname)
        
        xvals = dataframe.xs('x').values
        yvals = dataframe.xs('y').values
        zvals = dataframe.xs('z').values
        
        mcomfield.set_data(dataframe.xs('x_mcom').values, dataframe.xs('y_mcom').values)
        mcomfield.set_3d_properties(zs=np.array(dataframe.xs('z_mcom').values))
        return (mcomfield)

    anim = animation.FuncAnimation(fig, doframe,
                               frames=nframes, interval=20, blit=True)
    moviename = "%s.mp4"%filebase
    anim.save(moviename, fps=30, bitrate=4000)
    return moviename
