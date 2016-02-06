def massradius(pan, quantity='radius', fraction=0.1):
    times = pan[quantity].keys()
    high_mass_radius_list = []
    low_mass_radius_list = []
    nstars = pan[quantity][times[0]].count()
    nfrac = int(nstars * fraction)
    
    hmseries = pan[quantity][0:nfrac].median()
    lmseries = pan[quantity][-nfrac:-1].median()
    ratioseries = lmseries/hmseries
        #print time, hmr, lmr
        
#    lmseries = pd.Series(data=low_mass_radius_list, index=times)
#    hmseries = pd.Series(data=high_mass_radius_list, index=times)
#    ratioseries = pd.Series(data=ratios, index=times)
    return(ratioseries, lmseries, hmseries)

    def avg_series(ensname, output=False):
    storename = "%s-avg.h5"%ensname
    store = pd.HDFStore("%s-avg.h5"%ensname)
    try:
        ratiodf = store['ratiodf']
        lowdf = store['lowdf']
        highdf = store['highdf']
    except KeyError:
        ensfile = open(ensname, 'rb')
        runlist = pickle.load(ensfile)

        rsdict = {}
        lsdict = {}
        hsdict = {}
        i = 0
        for run in runlist:
            key = "%d"%i
            if output:
                print(key)
            try:
                thepan = run_to_panel(run)
                rseries, lmseries, hmseries = massradius(thepan)
                rsdict[key] = rseries
                lsdict[key] = lmseries
                hsdict[key] = hmseries
            except IOError:
                pass
            i+=1
        highdf = pd.DataFrame(hsdict)
        lowdf = pd.DataFrame(lsdict)
        ratiodf = pd.DataFrame(rsdict)
    
        # compute averages
        highdf['avg'] = highdf.mean(axis=1)
        lowdf['avg'] = lowdf.mean(axis=1)
        ratiodf['avg'] = ratiodf.mean(axis=1)
    
        # compute stddev
        highdf['stddev'] = highdf.std(axis=1)
        lowdf['stddev'] = lowdf.std(axis=1)
        ratiodf['stddev'] = ratiodf.std(axis=1)
 
        store['highdf'] = highdf
        store['lowdf'] = lowdf
        store['ratiodf'] = ratiodf
        
    return ratiodf, lowdf, highdf

def r_and_m(clusterstep):
    rvals = []
    masses = []
    
# determine the radii and masses of stars for a timestep in kira output
# uses extract_particle_dynamics to open story and create lists of stars
    
    partlist = extract_particle_dynamics(clusterstep)
    
    for particle in partlist:
        masses.append(particle[6])
        x = particle[0]
        y = particle[1]
        z = particle[2]
        r = np.sqrt(x*x + y*y + z*z)
        rvals.append(r)
#        print r, particle[6]
        
    return rvals, masses

def medianpos(mlow, mhigh, rad, masses):
    index = 0
    r_lowmass = []
    r_highmass = []
    
# find median radius for stars below a low mass cut-off and above
# a high-mass cut-off given the desired cut-offs as well as lists of
# radii and masses (ordered the same)
    
    for mass in masses:
        if mass <= mlow:
            r_lowmass.append(rad[index])
        if mass >= mhigh:
            r_highmass.append(rad[index])
        index = index + 1
        
    medlow = np.median(r_lowmass)
    medhigh = np.median(r_highmass)
    
    return medlow, medhigh

def medianpos_percentile(storylist):
    masscut = 0.1
    first = 1
    median_low = []
    median_high = []
    
# takes a storylist generated from kira output and produces a list of
# median star positions for stars in the upper & lower percentile as
# set in the parameter "masscut", above

# when looking at the initial timestep, it uses the percentile to figure
# out actual cut-offs in mass.  This way, we do not have to worry about 
# evaporation changing which stars fall in our observed bins.  
    
    for story in storylist:
        (radii, masses) = r_and_m(story)
        if first == 1:
            masssort = np.sort(masses)
            nummass = len(masses)
            indexlo = int(np.floor(masscut * nummass))
            indexhi = int(np.floor(nummass - indexlo))
            masslow = masssort[indexlo]
            masshigh = masssort[indexhi]
            #print masslow, masshigh
            first = 0
        (medlow, medhigh) = medianpos(masslow, masshigh, radii, masses)
        median_low.append(medlow)
        median_high.append(medhigh)
    return median_low, median_high
    
def quantile_radius(pan, quant):
    """Get the average radius for a given mass quantile.

    Compares the average radius for the given mass quantile 0% -> quant
    with that of the complement ((1-quant) -> 100%)

    Takes inputs:
    pan -- pandas panel, where the item index is sorted by mass
    quant -- the quantile, in percent, to use.

    returns a tuple of time series:
    (lightradius, heavyradius, light/heavy) 
    """
    indices = sorted(pan.keys(), key=int)
    number = int(quant*len(indices))
    #print "%d runs in requested quantile" % number
    heavyslice = [pan[index] for index in indices[:number]]
    lightslice = [pan[index] for index in indices[-number:]]
    
    #print "heavy masses:", [star['m'][0] for star in heavyslice]
    #print "light masses:", [star['m'][0] for star in lightslice]
    
    heavyr = np.zeros_like(heavyslice[0]['radius'].values)
    for star in heavyslice:
        heavyr += star['radius'].values
    heavyr /= number
    
    lightr = np.zeros_like(lightslice[0]['radius'].values)
    for star in lightslice:
        lightr += star['radius'].values
    lightr /= number
    
    ratio = lightr/heavyr
    return lightr, heavyr, ratio
