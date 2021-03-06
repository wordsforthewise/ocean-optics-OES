from datetime import datetime
import csv, matplotlib.dates, matplotlib, math, os, glob, re, sys
import easygui as eg
import pylab as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
import numpy as np
from matplotlib.widgets import Button
from datetime import datetime
sys.path.append("Y:/Nate/git/nuvosun-python-lib/")
import nuvosunlib as nsl

#matplotlib.rcParams.update({'font.size': 22})
#matplotlib.rcParams.update({'savefig.facecolor': 'k'})
global process
global dataFile
global elementDict

files = os.listdir('C:/OESdata')
for file in files:
    if re.search('MC\d\d.txt',file):
        tool = file[:4]

BEzoneList, PCzoneList, zoneToIndexMap, MPcomPort, BEintTime, BEnumScans, PCintTime, PCnumScans = nsl.load_OES_config(tool)

try:
    todaysRun = sys.argv[1]
    runNum = sys.argv[2]
    process = sys.argv[3]
except:
    runNum = None
    todaysRun = False
    process = ' '
        
savedate = datetime.strftime(datetime.now(),'%m-%d-%y') #made DT format similar to data system format
savedir = 'C:/OESdata/' + process + ' ' + savedate + '/'
onLocal = True
runToday = False
folders = os.listdir('C:/OESdata/')
for folder in folders:
    if re.search(savedate,folder):
        runToday = True
        savedir = 'C:/OESdata/' + folder + '/'
        print savedir
        process = re.search('([BP][EC])',folder).group(1)
        print process

if todaysRun == False and runToday:
    msg = "Use today's run?"
    title = "Use today's run?"
    todaysRun = eg.ccbox(msg, title, choices = ('yes','choose another run'))

if not todaysRun:
    onLocal = False
    if not os.path.isdir('C:/OESdata/'):
        default = 'Y:/Nate/new MC02 OES program/backup from MC02 computer/data'
    else:
        default = 'C:/OESdata/'
    savedir = eg.diropenbox(msg = 'choose a directory to load data from', title = 'load OES data', default = default)
    for f in glob.iglob(savedir + '\\' + '*.csv'):
        if re.search('OES signals', f):
            dataFile = f
            print dataFile
        if process == ' ':
            if re.search('BE',savedir):
                process = 'BE'
            elif re.search('PC',savedir):
                process = 'PC'
            else:
                BEproc = eg.ynbox(msg='Which process is this?', title='choose process', choices=('BE','PC'))
                if BEproc:
                    process = 'BE'
                elif not BEproc:
                    process = 'PC'
else:
    dataFile = savedir + savedate + ' -- OES signals.csv' 
    
def handle_close(evt):
    if runNum != None:
        basepath = 'Y:\\Experiment Summaries\\Year ' + str(datetime.now().year)
        runPath = basepath + '\\' + 'S' + str(runNum).zfill(5) + '\\'
        print runPath
        if os.path.exists(runPath):
            print 'found place to save it', runPath
            saveFile2 = runPath + '\\' + str(runNum) + ' ' + process + ' OES.png'
        else:
            print 'didn\'t find place to save. creating directory'
            runPath = basepath + '\\' + 'S' + str(runNum).zfill(5) + '\\'
            os.mkdir(runPath)
            saveFile2 = runPath + '\\' + str(runNum) + ' ' + process + ' OES.png'
        print 'saving at', saveFile2
        fig.savefig(saveFile2, facecolor = fig.get_facecolor(), edgecolor='none', bbox_inches = 'tight')
    if onLocal:
        saveFile = savedir + savedir[-8:-1] + ' ' + process + '.png'
    else:
        saveFile = savedir + '/' + savedir[-8:] + ' ' + process + '.png'
    print 'saving at:',saveFile
    fig.savefig(saveFile, facecolor = fig.get_facecolor(), edgecolor='none', bbox_inches = 'tight')
        
 
def create_oesdict():
    #make list of elements and zones measured
    global zoneList
    if process == 'BE':
        zoneList = BEzoneList
    elif process == 'PC':
        zoneList = PCzoneList
    if datetime.strptime(savedate,'%m-%d-%y') >= datetime(2015,7,1): # changed to new data storage format on July 1st, 2015
        global elementDict
        elementDict, normalizationKeys = nsl.OESparameters(True)
        elementList = elementDict.keys()
        measuredElementList = elementList + normalizationKeys
    else:
        elementList = ['Cu','In','Ga','Se','Ar','Na','Mo','Ti','O2','H2']
        measuredElementList = elementList #use this: ['Cu', 'In', 'Ga', 'Ar', 'O2', 'H2'] to restrict list as needed
    combinedList = [zone + ' ' + element for zone in zoneList for element in measuredElementList] #Combines list like 5A Cu, 5A In, etc...
    OESdataDict={}
    for zone in zoneList:
        OESdataDict[zone] = {}
        OESdataDict[zone]['DT'] = []
        for element in measuredElementList:
            OESdataDict[zone][element]= []
            
    return OESdataDict,zoneList,measuredElementList

def getdata():
    global dataFile
    OESdataDict,zoneList,measuredElementList=create_oesdict()
    with open(dataFile, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        firstRow = True
        for row in spamreader:
            if not firstRow and row[-1]!='':
                zoneCount = 0
                for zone in zoneList:
                    OESdataDict[zone]['DT'].append(datetime.strptime(row[0],'%m/%d/%y %H:%M:%S %p'))
                    for elCount in range(len(measuredElementList)):
                        OESdataDict[zone][measuredElementList[elCount]].append(row[1+zoneCount*len(measuredElementList)+elCount])
                    zoneCount += 1
            else: #skips first row which is labels
                firstRow = False
    '''for zone in zoneList:
        OESdataDict[zone]['DT']=np.array(OESdataDict[zone]['DT'])
        for element in measuredElementList:
            OESdataDict[zone][element]=np.array(OESdataDict[zone][element],dtype='float64')'''

    return OESdataDict
                
def plotdata(*args):
        plt.clf()
        OESdataDict = getdata()
        Cu3 = {}
        CuSum = 0
        InSum = 0
        GaSum = 0
        Cu3total = 0
        for zone in OESdataDict.keys():
            Cu3[zone] = float(OESdataDict[zone]['Cu-325-327'][-1])/(float(OESdataDict[zone]['In-451'][-1])+float(OESdataDict[zone]['Ga-417'][-1]))
            
            CuSum += float(OESdataDict[zone]['Cu-325-327'][-1]) / float(OESdataDict[zone]['Ar-811'][-1])
            InSum += float(OESdataDict[zone]['In-451'][-1]) / float(OESdataDict[zone]['Ar-811'][-1])
            GaSum += float(OESdataDict[zone]['Ga-417'][-1]) / float(OESdataDict[zone]['Ar-811'][-1])
            
            if zone != '6A': #exclude zone 6A for now cause it's junk
                Cu3total += Cu3[zone]
            Cu3[zone] = math.ceil(Cu3[zone]*100)/100.0
        Cu3total = Cu3total/3 #average from 4 zones
        Cu3total = math.ceil(Cu3total*100)/100.0
        Cu3Sumtotal = CuSum / (InSum + GaSum)
        Cu3Sumtotal = math.ceil(Cu3Sumtotal*100)/100.0
        Cu3total *=1.446

        # plot the data
        if datetime.strptime(savedate,'%m-%d-%y') >= datetime(2015,7,1): # changed to new data storage format on July 1st, 2015
            if process == 'PC':
                elementsToPlot = {'H-656/Fi' : elementDict['H-656']['color'], 'Cu-325-327/Fi' : elementDict['Cu-325-327']['color'], 'In-451/Fi' : elementDict['In-451']['color'], 'Ga-417/Fi' : elementDict['Ga-417']['color'], 'Na-589/Fi' : elementDict['Na-589']['color']}
            elif process == 'BE':
                elementsToPlot = {'Mo-380/Fi' : elementDict['Mo-380']['color'], 'Ti-496-522/Fi' : elementDict['Ti-496-522']['color'], 'H-656/Fi' : elementDict['H-656']['color'], 'Na-589/Fi' : elementDict['Na-589']['color']}
        else:
            if process == 'PC':
                elementsToPlot = {'Ar' : '#b2b2b2', 'Cu' : '#FFCC00', 'In': '#0099ff', 'Na' : '#009933', 'Ga' : '#ff5c33'} # dict of elements and colors for plotting
            elif process == 'BE':
                elementsToPlot = {'Ar' : '#b2b2b2', 'Mo' : '#0099ff', 'Ti' : '#ff5c33', 'Na' : '#009933'} # dict of elements and colors for plotting
        if process == 'PC':
            ax5A = plt.subplot2grid((2, 2), (0,0), axisbg='k')
            ax5B = plt.subplot2grid((2, 2), (1,0), axisbg='k')
            ax6A = plt.subplot2grid((2, 2), (0,1), axisbg='k')
            ax6B = plt.subplot2grid((2, 2), (1,1), axisbg='k')
            if datetime.strptime(savedate,'%m-%d-%y') >= datetime(2015,7,1):
                ax5AFi = ax5A.twinx()
                ax5BFi = ax5B.twinx()
                ax6AFi = ax6A.twinx()
                ax6BFi = ax6B.twinx()
        if process == 'BE':
            ax1B = plt.subplot2grid((2, 2), (0,0), axisbg='k')
            ax2B = plt.subplot2grid((2, 2), (1,0), axisbg='k')
            ax3B = plt.subplot2grid((2, 2), (0,1), axisbg='k')
            ax4B = plt.subplot2grid((2, 2), (1,1), axisbg='k')
            if datetime.strptime(savedate,'%m-%d-%y') >= datetime(2015,7,1):
                ax1BFi = ax1B.twinx()
                ax2BFi = ax2B.twinx()
                ax3BFi = ax3B.twinx()
                ax4BFi = ax4B.twinx()
        
        for zone in zoneList:
            OESdates = matplotlib.dates.date2num(OESdataDict[zone]['DT'])
        
            # changes ticks and axes to white color
            eval('ax' + zone).tick_params(color='w',labelcolor='w')
            for spine in eval('ax' + zone).spines.values():
                spine.set_edgecolor('w')
            if process == 'PC':
                eval('ax' + zone).set_ylim([0,0.15])
            
            
        
            eval('ax'+zone).xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            
            if datetime.strptime(savedate,'%m-%d-%y') >= datetime(2015,7,1):
                eval('ax' + zone + 'Fi').tick_params(color='w',labelcolor='w')
                for spine in eval('ax' + zone + 'Fi').spines.values():
                    spine.set_edgecolor('w')
                eval('ax'+zone+'Fi').plot_date(OESdates, OESdataDict[zone]['Fi'], color = elementDict['Fi']['color'])
                eval('ax'+zone+'Fi').plot_date(OESdates, OESdataDict[zone]['Fi'], '--', color = elementDict['Fi']['color'], linewidth = 4, label = 'Fi')
                if len(zoneList) < 2:
                    eval('ax' + zoneList[2] + 'Fi').set_ylabel('Full intensity (Fi) of plasma', color='w')
                else:
                    eval('ax' + zoneList[0] + 'Fi').set_ylabel('Full intensity (Fi) of plasma', color='w')
            
            for element in elementsToPlot.keys():
                eval('ax'+zone).plot_date(OESdates, OESdataDict[zone][element], color = elementsToPlot[element])
                eval('ax'+zone).plot_date(OESdates, OESdataDict[zone][element], '-', color = elementsToPlot[element], linewidth = 4, label = element)
                eval('ax'+zone).set_title(zone, color = 'w')
                eval('ax'+zone).grid(color='w', linewidth=2)
        
        eval('ax' + zoneList[0]).set_ylabel('OES integrated intensity', color='w')
        eval('ax' + zoneList[1]).set_xlabel('time', color='w')
        
        legend = eval('ax' + zoneList[0]).legend(bbox_to_anchor=(0.2, 1.1), loc='upper right', borderaxespad=0., shadow=True, labelspacing=0, numpoints=1)
        # The frame is matplotlib.patches.Rectangle instance surrounding the legend.
        frame = legend.get_frame()
        frame.set_facecolor('0.90')
            # Set the fontsize
        #for label in legend.get_texts():
        #   label.set_fontsize('25')
        #ax1.set_ylim([0,60])
        #ax1.axhline(45,ls='--',color='#ff0000',linewidth=4)
        
        if process == 'PC':
            cu3stringlist = [str(zone)+ ':' + str(Cu3[zone]) for zone in sorted(Cu3.keys())]
            cu3string = ''
            for each in cu3stringlist:
                cu3string += each + ' ' 
            plt.figtext(0.6,0.95,'Cu3: ' + cu3string,fontsize=12,color='white')
            plt.figtext(0.6,0.92,'overall Cu3: ' + str(Cu3total),fontsize=12,color='white')
        #plt.title('OES zone ' + zoneToPlot,color='w')
        fig.canvas.set_window_title('OES zones ' + zoneList[0] + ' - ' + zoneList[-1])
        
fig=plt.figure(facecolor='k')
fig.canvas.mpl_connect('close_event', handle_close)
try:
    print 'using qt4agg backend'
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
except AttributeError:
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')

ani = animation.FuncAnimation(fig, plotdata, interval=15000)
plt.show()