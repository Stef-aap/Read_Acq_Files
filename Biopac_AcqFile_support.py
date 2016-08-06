import ctypes
from ctypes import *
import numpy

from pylab import plot, show, figure
''''
//! Data structure that describes an ACQ file
struct ACQFILESTRUCT
{
	bool bPCFile; /**< flag to differ Acq 3.x for Win file and Acq 4.x files. if TRUE - Acq 39x file, FALSE - ACQ 4.x file */
	long numChannels; /**< number of channels */
	long mpHeaderLen; /**< length of the MP device header in bytes */
	long mpDevID;  /**< ID of the MP device that recorded the data (currently it is always set to zero) */
	HANDLE hFile;	/**< handle to the ACQ file */
	long version;	/**< ACQ file version */
	long fileHeaderLen; /**< length of the file information header in bytes*/
	long chHeaderLen; /**< length of the channel information header in bytes */
	long dataOffset; /**< offset of raw data from the beginning of the file in bytes */
	long markerLen;	/**< total length of all marker data in bytes */
	long numMarkers; /**< total number of markers */
	long markerOffset; /**< offset of the first marker from the beginning of the file in bytes */
	long journalLen; /**< length of the Journal text (not including the null character) */
	double sampleRate; /**< sample rate in msec/sample */
	long dataViewSectionLength;  /**< length of the Data View section in bytes */
	long splitPanelSectionLength; /**< Split panel file section must be skipped to properly read channel headers, starting with version of ACQ440 */
};
'''
k410R3ChannelLabelLength = 1024
k410R3ChannelUnitLength = 512
class ACQFILESTRUCT(Structure):
  _pack_ = 1
  _fields_ = [ ("bPCFile", c_bool),
                ("numChannels", c_long),
                ("mpHeaderLen", c_long),
                ("mpDevID", c_long),
                ("hFile", c_void_p),
                ("version", c_long),
                ("fileHeaderLen", c_long),
                ("chHeaderLen", c_long),
                ("dataOffset", c_long),
                ("markerLen", c_long),
                ("numMarkers", c_long),
                ("markerOffset", c_long),
                ("journalLen", c_long),
                ("sampleRate", c_double),
                ("dataViewSectionLength", c_long),
                ("splitPanelSectionLength", c_long)



                ]


#00 0200 0000 0000 0000 2400 0000 6804 0000 7c00 00006009000022070000dc170000df0300001900000044b81d00b71a0000000000000000004008000000280000000000000000000

class CHANNELSTRUCT_A(Structure):
  _pack_ = 1
  _fields_ = [
                ("num", c_long),
                ("index", c_long),
                ("numSamples", c_long),
                ("scale", c_double),
                ("offset", c_double),
                ("label", c_char*40),
                ("units", c_char*20),
                ("newComTxt", c_char * k410R3ChannelLabelLength),
                ("newUnitsTxt", c_char * k410R3ChannelUnitLength),
                ]


class MARKERSTRUCT(Structure):
  _pack_ = 1
  _fields_ = [
                ("textLength", c_long),
                ("location", c_long),
                ("index", c_long),
                ("textOffset", c_long),


                ]

ch = CHANNELSTRUCT_A()
acqfile = ctypes.windll.acqfile
a = ACQFILESTRUCT()


# it would be nice if could determine the 32/64 bit status of this DLL
print ( 'message from Biopac_AcqFile_support.py: Biopac File-DLL loaded' )

## should become a docstring
__doc__ = """
# Once you've created an Biopac-File-Object
  Filename = b"C:\\E\\_Biopac\\acq_opnamen\\4Channel.acq"
  MyFile = Biopac_File ( Filename )
# You can get information from that Biopac-File-Object,
# through the following methods:
  MyFile.Opened ()    # returns True or False
"""

class Biopac_File ( object ) :
  def __init__ ( self, Filename ) :
    if isinstance ( Filename, str ) :
      Filename = Filename.encode()
    self.Filename = Filename.decode()
    self.Data     = None
    self.acqfile = ctypes.windll.acqfile
    ##print ( self.acqfile, 'wist' )
    self.FileStruct = ACQFILESTRUCT()
    Opened = self.acqfile.initACQFile_A ( Filename, byref ( self.FileStruct ))
    self.Opened = Opened == 1

  def MetaData_Raw ( self ) :
    print ( '\nRaw File MetaData :', self.Filename )
    print ( 60 * '=' )
    for aa in dir ( self.FileStruct ) :
      if not aa.startswith ( '_' ) :
        print ( aa, ':', getattr ( self.FileStruct, aa ))

  def MetaData ( self ) :
    print ( '\nFile MetaData :', self.Filename )
    print ( 60 * '=' )
    print ( 'Number of Channels :', self.FileStruct.numChannels )
    print ( 'SampleRate         :', 1e3/self.FileStruct.sampleRate, 'Hz' )
    print ( 'Number of Markers  :', self.FileStruct.numMarkers )
    print ( 'Journal Length     :', self.FileStruct.journalLen )
    print ( 'Version            :', self.FileStruct.version )

  def Channel_MetaData ( self ) :
    MyChannels = []
    for i in range ( self.FileStruct.numChannels ) :
      ChannelInfo = CHANNELSTRUCT_A()
      self.acqfile.getChannelInfo_A ( i, byref ( self.FileStruct ), byref ( ChannelInfo ))

      print ( '\nChannel MetaData, Channel :', i )
      print ( 60 * '=' )
      print ( 'Label  :', ChannelInfo.label.decode () )
      print ( 'Units  :', ChannelInfo.units.decode () )
      print ( 'Scale  :', ChannelInfo.scale )
      print ( 'Offset :', ChannelInfo.offset )

  def Channel_MetaData_Raw ( self ) :
    MyChannels = []
    for i in range ( self.FileStruct.numChannels ) :
      ChannelInfo = CHANNELSTRUCT_A()
      self.acqfile.getChannelInfo_A ( i, byref ( self.FileStruct ), byref ( ChannelInfo ))

      print ( '\nRaw Channel MetaData, Channel :', i )
      print ( 60 * '=' )
      for aa in dir(ChannelInfo):
        if not aa.startswith('_'):
          print(aa, i, ':', getattr(ChannelInfo,aa))

  def Get_Journal ( self ) :
    Text = ( c_wchar * (( 50000 )) )()
    self.acqfile.getJournalText_W ( byref( self.FileStruct ),
                                    byref ( Text ) )
    print ( 'Journal :',  Text )
    return len(Text), Text

  def Get_Markers ( self ) :
    Markers = []

    for i in range ( self.FileStruct.numMarkers ) :
      MarkerInfo = MARKERSTRUCT()
      self.acqfile.getMarkerInfo ( i, byref ( self.FileStruct ), byref ( MarkerInfo ))
      Text = ( c_wchar * (( MarkerInfo.textLength+1)) )()  ## Extra char for \x00, terminating zero.
      self.acqfile.getMarkerText_W ( byref( self.FileStruct ), byref( MarkerInfo ),byref ( Text ))
      print ( 'Marker', i,  ':', MarkerInfo.location, Text.value)

  def Get_Data ( self ) :
    self.MyChannels = []
    for i in range ( self.FileStruct.numChannels ) :
      ChannelInfo = CHANNELSTRUCT_A()
      self.acqfile.getChannelInfo_A ( i, byref ( self.FileStruct ), byref ( ChannelInfo ))

      samples = c_double * ChannelInfo.numSamples
      MySamples = samples()
      self.acqfile.getAllSamples ( byref ( self.FileStruct ), byref ( ChannelInfo ), MySamples )
      Channel_Data = numpy.frombuffer ( MySamples )
      self.MyChannels.append ( Channel_Data )
      #print ( Channel_Data.shape )
    self.Data = numpy.vstack ( self.MyChannels ).T
    return self.Data

  def Plot ( self, Start = None, End = None, Middle = None, Width = None ) :
    if self.Data is None :
      Get_Data ()

    if Middle and Width :
      Start = Middle - Width / 2
      End   = Middle + Width / 2

    if Start and End :
      PlotData = self.Data [ Start : End ]
    elif Start :
      PlotData = self.Data [ Start : ]
    elif End :
      PlotData = self.Data [ : End ]
    else :
      PlotData = self.Data

    plot ( PlotData )
    show ()



# ***********************************************************************
# ***********************************************************************
if __name__ == "__main__":

  print ( __doc__ )  ##Biopac_Help )

  Filename = "C:\\E\\_Biopac\\acq_opnamen\\4Channel.acq"

  MyFile = Biopac_File ( Filename )
  print ( 'Biopac succesfully Opened :', MyFile.Opened )

  MyFile.MetaData ()
  #MyFile.MetaData_Raw ()

  MyFile.Channel_MetaData ()
  #MyFile.Channel_MetaData_Raw ()

  MyFile.Get_Markers ()

  MyFile.Get_Journal ()

  MyFile.Get_Data ()

  #MyFile.Plot ()
  MyFile.Plot ( Middle = 700, Width = 1000 )
