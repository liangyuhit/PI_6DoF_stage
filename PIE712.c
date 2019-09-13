typedef unsigned short int sdk_wchar_t;  
#define SDK_CONFLICT_PRIORITY
#include <windows.h>
#include <analysis.h>
#include <utility.h>
#include <ansi_c.h>
#include <formatio.h>
#include <cvirte.h>		
#include <userint.h>
#include<NIDAQmx.h>
#include "PI_GCS2_DLL.h"
#include "PIE712.h"
#include "E712_globals.h"
#include "PIstageWaveGenerator.h" 

#define max_wave_points 262144		// 2^18; aus Controller gelesen
#define nDataRecChan	12			// Number of data recorder channels; E712 hat 12 !
#define nDataRecMax		1398101		// Max. number per channel 2.0^23/6;
#define zmax			18.0		// Upper limit of PI-Stage in um
#define zmin			-2.0			// Lower limit of PI-Stage
#define	max_sent		10			// Max sent = 255 bytes;PI_TWS: 3xsize(int64) = 24bytes, 10*24 bytes=240bytes

// Interrupt function for data acquisition
int32 CVICALLBACK acq_data(TaskHandle taskHandle, int32 signalID, void *callbackData);

int pcolor[6]={VAL_RED, VAL_BLUE,VAL_DK_GREEN, VAL_GREEN, VAL_DK_RED, VAL_DK_BLUE};
char legends[6][6];

// Wave generator
#define nwavetables 6
//int WaveTableIds[nwavetables],MaxWaveTableSize[nwavetables];
//long WaveTableInterpolationType[nwavetables]={1,1,1,1,1,1};
int WaveGeneratorIds[6]={1,2,3,4,5,6}, WaveGeneratorRate[6],WaveGeneratorInterpolation[6],nwave_generators;
double *pdWavePoints=NULL;
//int WaveTableParameterId =1;
int zWaveGenId=4;
int WG_StartModus = 0; //0: stop, 1: start immediately, 2: start by trigger on In1, In2
double TControl = 0.07;									// Time constant of E712 Controller im msec
double TIllumination = 9.8, TFrameTransfer = 30.0;		// Illumination Time of and Frame Transfer Time of Pulnix CCD-Camera
int nIllumination, nFrameTransfer;
double TL = 1.4; // Lead time before and after illumination
int nwavepoints=0; 

// Data recorder
int data_rec_rate = 1;

// NI-Counters
TaskHandle				taskHandleCTR0 = 0;
TaskHandle				taskHandleCTR1 = 0;
TaskHandle				taskHandleCTR2 = 0;
TaskHandle				taskHandleDigitalOutput = 0;
int								iTestRegisterSignalEventForCTR0 = 0;
unsigned char			ucDigitalOutputState = 1;
int32							iNbSamplesWrittenSuccessfully = 0;
//static int					iTestAcqData = 0;	
static int32				iNbCounted = 0;
int								*piFirstTriggerPulse, *piLastTriggerPulse; 	// First / last index of trigger during illumination
int								*piNTriggerPulse;										// Value of pulse for each illumination period	
int								nPulseCounted = 0;									// Value of pulses during illumination
int								*Index,*iWaveTableIndex;							// Index of values during illumantion
int32							iTestNbRead=0;
int								iNbOfPulses = 0;									// Number of Trigger pulses during illumination 
uInt32						*piIndexRecordedByCTR2;						// index_used
int								iTestPulseGenerating = 0;
unsigned int				iLowTicksCounterPulses = 6;					// 0.1 msec with a clock of 100kHz (10microsec)  -> 0.1/0.01=10
unsigned int				iHighTicksCounterPulses = 2;				// 0.02 msec with a clock of 100kHz (10microsec) -> 0.02/0.01=2
uInt32						iHighTicks = 1000;							// 10 msec with a clock of 100kHz (10microsec)  -> 10/0.01
uInt32						iLowTicks = 3500;//3386;					// 33.86 msec with a clock of 100kHz (10microsec) -> 35/0.01
static int					iTestAcqData = 0;
int								ii,jj,kk;
double						*xavgs, dAvgX, dVarzX, *yavgs, dAvgY,dVarzY, *zavgs, dAvgZ,dVarzZ; 

//int FrequencyTableRatePICalculation(int iNbOfSteps, double dTimeIllumination, double dTimeNoIllumination);
int generate_z_waveform_and_triggers(double TIllumination, double TFrameTransfer, double TControl,double zstart, double zstep, unsigned short nzsteps);

#ifndef PIErrChk
#define PIErrChk(functionCall) if ((bOK = functionCall) == FALSE) { goto ErrorPI; } else
#endif

#ifndef  DAQmxErrChk
#define DAQmxErrChk( functionCall) if( DAQmxFailed(iError=(functionCall)) ) goto ErrorDAQmx; else
#endif


int main (int argc, char *argv[])
{
	//int i=0;
	
	if (InitCVIRTE (0, argv, 0) == 0)
		return -1;	/* out of memory */
	if ((hE712pnl = LoadPanel (0, "PIE712.uir", E712_PNL)) < 0)
		return -1;
	
	DisplayPanel (hE712pnl);
	
 	//Connect PI-Controller
	if (PIConnectionType == RS232){ 
		PIConID = PI_ConnectRS232 (PI_ConCom, PI_ConBdrate);
	}
	//PIConID = PI_ConnectUSB(szDescriptionUSB);    
	
	if (PIConnectionType == USB){
		nUSBControllers = PI_EnumerateUSB(USB_Controllers,sizeof(USB_Controllers),"");
		if (nUSBControllers >= 0)
			PIConID = PI_ConnectUSB(szDescriptionUSB); 
		else{
			SetCtrlVal(hE712pnl,E712_PNL_PIMSGBOX,"Error opening PI Controller \n");
		}
	}
	if (PIConnectionType == TCPIP){
		PIConID = PI_ConnectTCPIP(szHostname,port); 
	}    
	//**** Connect to PI-Controller and setup
	if ( PIConID < 0 ) {   // Connect failed
		Fmt(szMsg,"%s<%s%d%s","Error connecting to the PI-Controller: \n",PIConID,"\n");
		SetCtrlVal (hE712pnl, E712_PNL_PIMSGBOX, "Error connecting to the PI-Controller: \n");
		SetCtrlVal (hE712pnl, E712_PNL_PIMSGBOX, szMsg);
	}
	else { // Connection established
			// Turn control loops on
			//     BOOL PI_SVO (int ID, const char* szAxes, const BOOL* pbValueArray)
		if (!PI_SVO(PIConID,szAllAxes,pbArrayServoON) ) {
			iError = PI_GetError(PIConID);
			PI_TranslateError(iError, szMsg, 1024);
			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
		}
		else{		;
			PI_qPOS(PIConID,"",pdPIPositionArray);
			SetCtrlVal(hE712pnl, E712_PNL_NXPOS,pdPIPositionArray[0]);
			SetCtrlVal(hE712pnl, E712_PNL_NYPOS,pdPIPositionArray[1]); 
			SetCtrlVal(hE712pnl, E712_PNL_NZPOS,pdPIPositionArray[3]); 
		}
		/* Read max. points in wave table; error function knwon
		for (i=0;i<nwavetables; i++)
			WaveTableIds[i]=i+1;
		
		if (!PI_qWMS(PIConID,WaveTableIds,MaxWaveTableSize,nwavetables )){
			iError = PI_GetError(PIConID);
			PI_TranslateError(iError, szMsg, 1024);
			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
		}
		else {
			Fmt(szMsg,"%s<%s%d%s","Max. number of values in wave table: \n",MaxWaveTableSize[0],"\n");
			SetCtrlVal (hE712pnl, E712_PNL_PIMSGBOX, szMsg);
		}   */
		
		// Read data recorder time multiplier
		if (!PI_qRTR(PIConID,&data_rec_rate )){
			iError = PI_GetError(PIConID);
			PI_TranslateError(iError, szMsg, 1024);
			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
		}
		else {
			Fmt(szMsg,"%s<%s%d%s","Data recorder rate divider:\t",data_rec_rate,"\n");
			SetCtrlVal (hE712pnl, E712_PNL_PIMSGBOX, szMsg);
		}  
		
		// Read wave generator time multiplier
		if (!PI_qWTR(PIConID,WaveGeneratorIds,WaveGeneratorRate,WaveGeneratorInterpolation,nwave_generators )){
			iError = PI_GetError(PIConID);
			PI_TranslateError(iError, szMsg, 1024);
			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
		}
		else {
			Fmt(szMsg,"%s<%s%d%s","Wave generator rate divider:\t",WaveGeneratorRate[0],"\n");
			SetCtrlVal (hE712pnl, E712_PNL_PIMSGBOX, szMsg);
		}
	
	}
	//
	//****************************************************************************************************************** 
	// DAQmx DIGITAL OUTPUT -> to start the CCD shutter timer and wave generator of the PI stage on falling edge
	//****************************************************************************************************************** 
	DAQmxErrChk (DAQmxCreateTask("DigitalOutput_task",&taskHandleDigitalOutput));
	DAQmxErrChk (DAQmxCreateDOChan(taskHandleDigitalOutput,"Dev1/port0/line0", "DigitalOutput0", DAQmx_Val_ChanPerLine));
	DAQmxErrChk (DAQmxStartTask(taskHandleDigitalOutput));
	ucDigitalOutputState = 1;
	DAQmxErrChk (DAQmxWriteDigitalLines(taskHandleDigitalOutput, 1, 1, 10.0, DAQmx_Val_GroupByChannel, &ucDigitalOutputState, &iNbSamplesWrittenSuccessfully, 0));

	//*******************************************************************************************************************************
	// DAQmx counter configure Code for CCD SHUTTER / CCD Illumination timer connected to Helios grabber. It triggers only the grabber.
	// The grabber provides the illumination pulse. It is inverted because it needs to trigger the PI Controller
	//*******************************************************************************************************************************
	DAQmxErrChk (DAQmxCreateTask("",&taskHandleCTR0));
	DAQmxErrChk (DAQmxCreateCOPulseChanTicks (taskHandleCTR0, "Dev1/ctr0", "ShutterCCD", NULL, DAQmx_Val_Low, 0, iLowTicks, iHighTicks));
	DAQmxErrChk (DAQmxSetCOCtrTimebaseSrc(taskHandleCTR0,"Dev1/ctr0","100kHzTimeBase"));
	//**** Configures the task to start acquiring or generating samples on a rising or falling edge of a digital signal.
	//**** ***  Start on pulse on PFI38 = CRT0 GATE on falling edge
	DAQmxErrChk (DAQmxCfgDigEdgeStartTrig(taskHandleCTR0,"/Dev1/PFI38",DAQmx_Val_Falling));		//DAQmx_Val_Rising; Start on falling edge
	//**** Sets only the number of samples to acquire or generate without specifying timing. 
	//     int32 DAQmxCfgImplicitTiming (TaskHandle taskHandle, int32 sampleMode, uInt64 sampsPerChanToAcquire);
	DAQmxErrChk (DAQmxCfgImplicitTiming(taskHandleCTR0,DAQmx_Val_ContSamps,1000));
	DAQmxErrChk (DAQmxStartTask(taskHandleCTR0));
	iTestPulseGenerating = 1;

	//********************************************************************************************************************************************  
	// DAQmx counter configuration code to deliver trigger pulses during the illumination time. Used to save counted pulses of the PI
	//********************************************************************************************************************************************  
	iLowTicksCounterPulses = 5;				//** 0.05 msec with a clock of 100kHz (10microsec)  -> 0.05/0.01
 	iHighTicksCounterPulses = 2;				//** 0.01 msec with a clock of 100kHz (10microsec) -> 0.01/0.01
	DAQmxErrChk (DAQmxCreateTask("",&taskHandleCTR1));
	DAQmxErrChk (DAQmxCreateCOPulseChanTicks(taskHandleCTR1,"Dev1/Ctr1","PulsesDuringCCDIllumination", NULL,DAQmx_Val_High,0,iLowTicksCounterPulses,iHighTicksCounterPulses));
	DAQmxErrChk (DAQmxSetCOCtrTimebaseSrc(taskHandleCTR1,"Dev1/Ctr1","100kHzTimeBase"));
	// Pulse generation only if illumination signal is high
	DAQmxErrChk (DAQmxSetPauseTrigType(taskHandleCTR1,DAQmx_Val_DigLvl));  
	DAQmxErrChk (DAQmxSetDigLvlPauseTrigSrc(taskHandleCTR1, "/Dev1/Ctr0InternalOutput"));
	DAQmxErrChk (DAQmxSetDigLvlPauseTrigWhen(taskHandleCTR1, DAQmx_Val_Low));
	DAQmxErrChk (DAQmxCfgImplicitTiming(taskHandleCTR1,DAQmx_Val_ContSamps,10));
	//**** *** PFI34 = CTR1 GATE
	//DAQmxErrChk (DAQmxStartTask(taskHandleCTR1));

	//****************************************************************************************
	// DAQmx counter configure code to count PI trigger pulses (PI Out1 -> SOURCE & Ouput CTR1 -> GATE
	//****************************************************************************************
	DAQmxErrChk (DAQmxCreateTask("",&taskHandleCTR2));
	DAQmxErrChk (DAQmxCreateCICountEdgesChan (taskHandleCTR2, "/Dev1/Ctr2", "CounterPI_Trigger_Pulse", DAQmx_Val_Rising, 0, DAQmx_Val_CountUp));
	DAQmxErrChk (DAQmxResetChanAttribute (taskHandleCTR2, "", DAQmx_CI_CountEdges_Term));
	//**** *** PFI30 = CTR2 GATE  (= P0.30)
	DAQmxErrChk (DAQmxCfgSampClkTiming (taskHandleCTR2, "/Dev1/Ctr1InternalOutput", 1e6, DAQmx_Val_Rising, DAQmx_Val_ContSamps, 1e5));

	//****************************************************************************************
	// Generating pulses with the National Instrument Card
	//****************************************************************************************
	Delay(0.01);
	ucDigitalOutputState = 0;
	DAQmxErrChk (DAQmxWriteDigitalLines(taskHandleDigitalOutput, 1, 1, 10.0, DAQmx_Val_GroupByChannel, &ucDigitalOutputState, &iNbSamplesWrittenSuccessfully, 0));
	// Reset 
	Delay(0.01);
	ucDigitalOutputState = 1;
	DAQmxErrChk (DAQmxWriteDigitalLines(taskHandleDigitalOutput, 1, 1, 10.0, DAQmx_Val_GroupByChannel, &ucDigitalOutputState, &iNbSamplesWrittenSuccessfully, 0));
	SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Generating pulse train...\n");	
	
	sprintf(legends[0],"%s","x");
	sprintf(legends[1],"%s","y");
	sprintf(legends[3],"%s","z");
	sprintf(legends[4],"%s","rot x");
	sprintf(legends[5],"%s","rot y");
	sprintf(legends[2],"%s","rot z");
	
	ErrorDAQmx:
	if( DAQmxFailed(iError) )	{
		DAQmxGetExtendedErrorInfo(szErrBuff,2048);
		Fmt(szMsg,"%s<%s%s%s","DAQmx Error:",szErrBuff, "\n");
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
	}
	RunUserInterface ();
	DiscardPanel (hE712pnl);
	if (pdWavePoints)
		free(pdWavePoints);
	return 0;
}

int CVICALLBACK set_pos (int panel, int control, int event, void *callbackData, int eventData1, int eventData2)
{
	switch (event){
		case EVENT_COMMIT:
			switch (control){
				case E712_PNL_NXPOS:
					GetCtrlVal(hE712pnl, E712_PNL_NXPOS,&dPIPosX);
					PI_MOV(PIConID,"1",&dPIPosX);
				break;
				case E712_PNL_NYPOS:
					GetCtrlVal(hE712pnl, E712_PNL_NYPOS,&dPIPosY);
					PI_MOV(PIConID,"2",&dPIPosY);  
				break;
				case E712_PNL_NZPOS:
					GetCtrlVal(hE712pnl, E712_PNL_NZPOS,&dPIPosZ);
					PI_MOV(PIConID,"4",&dPIPosZ);
				break;
					case E712_PNL_NXROT:
					GetCtrlVal(hE712pnl, E712_PNL_NXROT,&dPIPosX);
					PI_MOV(PIConID,"5",&dPIPosX);
				break;
				case E712_PNL_NYROT:
					GetCtrlVal(hE712pnl, E712_PNL_NYROT,&dPIPosY);
					PI_MOV(PIConID,"6",&dPIPosY);  
				break;
				case E712_PNL_NZROT:
					GetCtrlVal(hE712pnl, E712_PNL_NZROT,&dPIPosZ);
					PI_MOV(PIConID,"3",&dPIPosZ);
				break;
			}
			Sleep(100);
			PI_qPOS(PIConID,"",pdPIPositionArray);
			SetCtrlVal(hE712pnl, E712_PNL_NXPOS,pdPIPositionArray[0]);
			SetCtrlVal(hE712pnl, E712_PNL_NYPOS,pdPIPositionArray[1]); 
			SetCtrlVal(hE712pnl, E712_PNL_NZPOS,pdPIPositionArray[3]); 
			SetCtrlVal(hE712pnl, E712_PNL_NXROT,pdPIPositionArray[4]);
			SetCtrlVal(hE712pnl, E712_PNL_NYROT,pdPIPositionArray[5]); 
			SetCtrlVal(hE712pnl, E712_PNL_NZROT,pdPIPositionArray[2]); 
		break;
	}
	return 0;
}

int CVICALLBACK PIE712_quit (int panel, int control, int event, void *callbackData, int eventData1, int eventData2)
{
	switch (event) {
		case EVENT_COMMIT:
			QuitUserInterface (0);
		break;
	}
	return 0;
}

int CVICALLBACK Read_data_rec_conf (int panel, int control, int event, void *callbackData, int eventData1, int eventData2)
{
	int qRecIds[nDataRecChan]={1,2,3,4,5,6,7,8,9,10,11,12},qRecOpt[nDataRecChan];  		//2 aktuelle Werte der Achse 
	//int RecBufSize=nDataRecChan, RecOptSize=nDataRecChan ;
	char qRecordSrcIds[1024]={'\0'};
	
	switch (event) {
		case EVENT_COMMIT:
			if (PI_qDRC (PIConID,qRecIds, qRecordSrcIds, qRecOpt, sizeof(qRecordSrcIds), nDataRecChan)){
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,qRecordSrcIds);
				
			}
			else {
				iError = PI_GetError(PIConID);
				PI_TranslateError(iError, szMsg, 1024);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error reading the Data recorder configuration\n");   
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n"); 
				return 0;
			}

		break;
	}
	return 0;
}

int CVICALLBACK read_data_rec_trig (int panel, int control, int event, void *callbackData, int eventData1, int eventData2)
{
	int qRecIds[nDataRecChan]={1,2,3,4,5,6,7,8,9,10,11,12},qTrigSrc[nDataRecChan];  		//2 aktuelle Werte der Achse 
	//int RecBufSize=nDataRecChan, RecOptSize=nDataRecChan ;
	char qRecordSrcIds[1024]={'\0'};
	
	switch (event) {
		case EVENT_COMMIT:
			if (PI_qDRT (PIConID,qRecIds, qTrigSrc, qRecordSrcIds, nDataRecChan, sizeof(qRecordSrcIds))){
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,qRecordSrcIds);
			}
			else {
				iError = PI_GetError(PIConID);
				PI_TranslateError(iError, szMsg, 1024);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error reading the trigger configuration\n");   
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n"); 
				return 0;
			}

		break;
	}
	return 0;
}

int CVICALLBACK record_data (int panel, int control, int event, void *callbackData, int eventData1, int eventData2)
{
	int *RecIds, *RecOpt,qRecOpt[nDataRecChan];  //qRecIds[nDataRecChan], 2 aktuelle Werte der Achse 
	//int RecBufSize=nDataRecChan, RecOptSize=nDataRecChan ;
	char *SrcIds; 			// Achsen 1 bis 6 werden den Tables 1-6 zugeordnet
	int DataRecChanSelect[nDataRecChan]={0,0,0,0,0,0};		// Which channels to read
	int *TrigSrc;//[nDataRecChan]={4,4,4,4,4,4};	//
	char *TrigVal;//={"0\n0\n0\n0\n0\n0\n"};	// dummy values if trig source = 4: function cal of DRT triggers start
	//BOOL res=FALSE;
	char qSrcIds[1024];
	int n2record=1000, max_recorded=0;// nrecorded[nDataRecChan] ={0}, min_recorded=0;						// Number of values to record
	int NfRecTables=0;
	int i=0,k=0;									// loop variables
	//char HDRText[1024];
	char GCSHeader[1024];
	double **RecData, *data,*tme, *freq,**FFTAmp=NULL,**FFTPhase=NULL;
	double df=0;
//	int pcolor[6]={VAL_RED,VAL_BLUE,VAL_DK_GREEN, VAL_GREEN, VAL_DK_RED, VAL_DK_BLUE};
//	char legends[6][6];
	int hPlot=0;
	int is_fft=0;
	
	switch (event) {
		case EVENT_COMMIT:
			/* Get options of current Controller
			PI_qHDR (PIConID, HDRText, (int)sizeof(HDRText));
			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,HDRText);
			
			#RecordOptions 
			1=Target Position of axis 
			2=Current Position of axis 
			3=Position Error of axis 
			7=Control Voltage of output chan 
			13=DDL Output of axis 
			14=Open Loop Control of axis 
			15=Control Output of axis 
			16=Voltage of output chan 
			17=Sensor Normalized of input chan 
			18=Sensor Filtered of input chan 
			19=Sensor ElecLinear of input chan 
			20=Sensor MechLinear of input chan 
			22=Slowed Target position of axis 
			23=Target velocity of axis 
			24=Target acceleration of axis 
			25=Target jerk of axis 
			26=Value of Digital Input 
			27=Value of Digital Output 
			
			#TriggerOptions 
			0=Default Setting 
			1=Any CMD Changing Pos 
			3=External Trigger 
			4=Immediate Trigger 
			
			#Parameters to be set with SPA 
			0x16000000=Data Recorder Table Rate 
			0x16000300=Data Recorder Chan Number 
			0x16000700=DRC Data Source 
			0x16000701=DRC Record Option 
			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n");       
			*/
			
			for (i=0;i<nDataRecChan;i++){
				DataRecChanSelect[i] = 0; 
			}
			
			GetCtrlVal(hE712pnl, E712_PNL_NDRVAL, &n2record);
			// Read channel selection
			GetCtrlVal(hE712pnl, E712_PNL_DR_X_SELECT,&DataRecChanSelect[0]);
			GetCtrlVal(hE712pnl, E712_PNL_DR_Y_SELECT,&DataRecChanSelect[1]);     
			GetCtrlVal(hE712pnl, E712_PNL_DR_Z_SELECT,&DataRecChanSelect[3]);     
			GetCtrlVal(hE712pnl, E712_PNL_DR_RX_SELECT,&DataRecChanSelect[4]);     
			GetCtrlVal(hE712pnl, E712_PNL_DR_RY_SELECT,&DataRecChanSelect[5]);     
			GetCtrlVal(hE712pnl, E712_PNL_DR_RZ_SELECT,&DataRecChanSelect[2]);
			GetCtrlVal(hE712pnl, E712_PNL_DR_FFTBOX,&is_fft);
			
			// Determine how many channels are used
			NfRecTables = 0; 
			for (i=0;i<nDataRecChan;i++){
				if (DataRecChanSelect[i] == 1 ) {
					NfRecTables++;
				}
			} 
			// Acquire an fill configuration arrays
			RecIds = (int *) malloc(NfRecTables*sizeof(int));
			SrcIds = (char *)malloc((2*NfRecTables+1)*sizeof(char)); 
			//qSrcIds = (char *)malloc((2*NfRecTables+1)*sizeof(char));
			RecOpt = (int *)malloc(NfRecTables*sizeof(int)); 
			TrigSrc =  (int *) malloc(NfRecTables*sizeof(int));
			TrigVal = (char *)malloc((2*NfRecTables+1)*sizeof(char));  
			
			k=0;	
			for (i=0;i<nDataRecChan;i++){
				if (DataRecChanSelect[i] == 1 ) {
					RecIds[k] = k+1;
					RecOpt[k] = 2;			// Current position data
					TrigSrc[k] = 4;			// Recording starts immediately  
					SrcIds[2*k]= (char)i+48+1;
					SrcIds[2*k+1]='\n';
					TrigVal[2*k] = 48;		// Dummy Value; muss offentsichtlich eine Zahl sein
					TrigVal[2*k+1]='\n';
					k++;
				}
			} 
			SrcIds[2*NfRecTables]='\0';
			//qSrcIds[2*NfRecTables]='\0'; 
			TrigVal[2*NfRecTables]='\0';
			
			// allocate memory for
			data = (double *)malloc(sizeof(double)); 
			RecData = (double **)calloc(n2record/2,sizeof(double *)); 
			if (is_fft){
				FFTAmp = (double **)calloc(n2record/2,sizeof(double *));
				FFTPhase = (double **)calloc(n2record/2,sizeof(double *));
			}
			for (i=0;i<NfRecTables;i++){
				RecData[i]= (double *)calloc(n2record,sizeof(double));
				if (is_fft){
					FFTAmp[i] = (double *)calloc(n2record/2,sizeof(double));
					FFTPhase[i] = (double *)calloc(n2record/2,sizeof(double));
				}
			}
			tme = (double *)calloc(n2record,sizeof(double));
			freq = (double *)calloc(n2record/2,sizeof(double));     
			
			//setup data recorder
			if( PI_DRC (PIConID, RecIds, SrcIds, RecOpt)){
				if (PI_qDRC (PIConID , RecIds, qSrcIds, qRecOpt, sizeof( qSrcIds),NfRecTables)){
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Data recorder configured for axis:\n");
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX, qSrcIds);
				}
				else {
					iError = PI_GetError(PIConID);
					PI_TranslateError(iError, szMsg, 1024);
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error reading the Data recorder configuration\n");   
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n"); 
					return 0;
				}
			}
			else {
				iError = PI_GetError(PIConID);
				PI_TranslateError(iError, szMsg, 1024);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error during setup of the data recorder\n");   
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n");  
				return 0;
			}
			
			// Setup Trigger options and poll number of values
			if (PI_DRT (PIConID, RecIds, TrigSrc, TrigVal,NfRecTables)){  // Starts data recording
				// Start asynchronous read
				
				if (PI_qDRR (PIConID,RecIds,NfRecTables, 1, n2record, &data, GCSHeader,1024)){
					do {
						Delay(0.001);
						PI_qDRL (PIConID,  RecIds, RecOpt,NfRecTables);
						if ( NfRecTables==1) {
							max_recorded=*RecOpt;
						}
						if ( NfRecTables>1) {
							max_recorded=RecOpt[NfRecTables-1];
						}
						SetCtrlVal(hE712pnl,E712_PNL_NDRVAL, max_recorded);
					} while (max_recorded < n2record);
					// Daten gelesen
					SetCtrlVal(hE712pnl, E712_PNL_NDRVAL,n2record);
					
					// Rearrange data in array
					if (NfRecTables == 1){
						memcpy(RecData[0],data,n2record*sizeof(double));
					}
					else{
						for (i=0;i<n2record;i++){
							for (k=0;k<NfRecTables;k++){
								RecData[k][i]=data[i*NfRecTables+k];
							}
						}
					}
					for (i=0;i<n2record; i++)
						tme[i]=TControl*i;
					
					if (is_fft){
						for (i=0;i<n2record/2; i++)
						freq[i]=1000.0/(TControl*n2record)*(i+1);
						
					}
					// Plot data
					DeleteGraphPlot (hE712pnl, E712_PNL_PI_GRPH, -1, VAL_IMMEDIATE_DRAW);
					if (is_fft){
						// Set Properties of 2nd Diagramm
						SetCtrlAttribute (hE712pnl, E712_PNL_PI_GRPH2, ATTR_XNAME, "Time in msec");
						SetCtrlAttribute (hE712pnl, E712_PNL_PI_GRPH2, ATTR_YNAME, "Position in um");
						SetCtrlAttribute (hE712pnl, E712_PNL_PI_GRPH2, ATTR_XMAP_MODE, VAL_LOG);
						SetCtrlAttribute (hE712pnl, E712_PNL_PI_GRPH2, ATTR_YMAP_MODE, VAL_LOG);
						DeleteGraphPlot (hE712pnl, E712_PNL_PI_GRPH2, -1, VAL_IMMEDIATE_DRAW); 
					}
					k=0;
					for (i=0;i<nDataRecChan;i++){
						if (DataRecChanSelect[i] ){
							hPlot = PlotXY (hE712pnl, E712_PNL_PI_GRPH, tme, RecData[k], n2record, VAL_DOUBLE, VAL_DOUBLE, VAL_THIN_LINE, VAL_NO_POINT,
											VAL_SOLID, 1, pcolor[i]);
							SetPlotAttribute (hE712pnl, E712_PNL_PI_GRPH, hPlot, ATTR_PLOT_LG_TEXT, legends[i]);
							if (is_fft){
								AmpPhaseSpectrum ( RecData[k], n2record, 1, TControl/1000, FFTAmp[k], FFTPhase[k], &df);
								hPlot = PlotXY (hE712pnl, E712_PNL_PI_GRPH2, freq, FFTAmp[k], n2record/2, VAL_DOUBLE, VAL_DOUBLE, VAL_THIN_LINE, VAL_NO_POINT,
											VAL_SOLID, 1, pcolor[i]);
							 SetPlotAttribute (hE712pnl, E712_PNL_PI_GRPH2, hPlot, ATTR_PLOT_LG_TEXT, legends[i]);
							}
							k++; 
						}
					}
				}
				else{
					iError = PI_GetError(PIConID);
					PI_TranslateError(iError, szMsg, 1024);
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Asynchrous read did not start:\n");   
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n"); 
					return 0;
				}
			}
			else { // Start failed
				iError = PI_GetError(PIConID);
				PI_TranslateError(iError, szMsg, 1024);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Data recording did not start:\n");   
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n"); 
				return 0;
			}
		
			free(RecIds);
			free(SrcIds); 
			free(RecOpt); 
			free(TrigSrc);
			free(TrigVal);  
			
			for (i=0;i<NfRecTables;i++){
				free(RecData[i]);
				if (is_fft){
					free(FFTAmp[i]);
					free(FFTPhase[i]);
				}
			}
			
			free(RecData);
			if (is_fft){
				free(FFTAmp);
				free(FFTPhase);
			}
			free(freq);
			free(tme);
			//free(data);
			
			
		break;
	}
	return 0;
}

int generate_z_waveform_and_triggers(double TIllumination, double TFrameTransfer, double TControl,double zstart, double zstep, unsigned short nzsteps){
	// Wave generator
	#define nwavetables 6
	//int WaveTableIds[nwavetables];
	int WaveTableInterpolationType[nwavetables]={1,1,1,1,1,1};
	//int WaveGeneratorIds[6]={1,2,3,4,5,6}, 
	int WaveGeneratorRate[6];//,WaveGeneratorInterpolation[6];
	//int WaveTableParameterId =1;
	int zWaveGenId=4;
	int nWGCycles=1;
	int iOffsetOfFirstPointInWaveTable, iNumberOfWavePoints, iAppendWave, iNumberOfSpeedUpDownPointsOfWave, iSegmentLength;
	int nwavepoints=0, nsent, nsent_last;
	double dAmplitudeOfWave, dOffsetOfWave, *TrigParameterVal,*pdTriggerVals;
	// Output trigger
	int	*TrigChannelIds, *TrigPointNumber, *TrigVal,*TrigParameter, nTrigVals=0, nTrigParameter;
	char GCSHeader[1024];  
	int hPlot;
	int i,k;
	double zend=0;
	//FILE *fp=NULL;
	
	WaveGeneratorRate[3] = 1;
	zend = zstart + nzsteps*zstep;
			
	if (zend > zmax || zend < zmin){
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Last Value out of range \n"); 
	}
	if (zstart > zmax || zstart < zmin){
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"First Value out of range \n"); 
	}
	
	// Move in start position
	PI_MOV(PIConID,"4\n",&zstart); 
	
	// Test if required points are smaller than the max. available points
	iSegmentLength = (int)((TIllumination + TFrameTransfer)/TControl);
	nwavepoints = (nzsteps +1)*iSegmentLength;
	
	if (nwavepoints > max_wave_points){ // Wave generator rate needs to be adjusted !
		WaveGeneratorRate[3] = (int)ceil((double)nwavepoints / max_wave_points);
		if (!PI_WTR(PIConID,&zWaveGenId, (&WaveGeneratorRate[3]), &WaveTableInterpolationType[3], 1)){   
			iError = PI_GetError(PIConID);
			PI_TranslateError(iError, szMsg, 1024);
			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error writing the wave table offset\n"); 
			return 0;
		}
	}
	
	// Delete wave table content
	if (!PI_WCL (PIConID, &zWaveGenId, 1)){
		iError = PI_GetError(PIConID);
		PI_TranslateError(iError, szMsg, 1024);
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error erasing wave table\n"); 
		return 0;
	}
			
	// write segments in wave table
	dAmplitudeOfWave = zstep;
	iAppendWave = 0;			// appends segment and concatenates segments
	nIllumination = (int)(TIllumination /(TControl*WaveGeneratorRate[3]));
	nFrameTransfer =(int)( TFrameTransfer/(TControl*WaveGeneratorRate[3]));
	iSegmentLength  = nIllumination + nFrameTransfer ; 		//
	iOffsetOfFirstPointInWaveTable =  nIllumination;
	iNumberOfWavePoints =  nFrameTransfer;  														// equals 34 msec
	iNumberOfSpeedUpDownPointsOfWave = (int)(500.0/ WaveGeneratorRate[3]); 	// equals 14 msec
	
	for (i=0;i<nzsteps;i++){
		dOffsetOfWave = i*zstep + zstart;   
		if (!PI_WAV_LIN (PIConID, zWaveGenId, iOffsetOfFirstPointInWaveTable,iNumberOfWavePoints, iAppendWave, 
						 iNumberOfSpeedUpDownPointsOfWave, dAmplitudeOfWave, dOffsetOfWave, iSegmentLength)){
			iError = PI_GetError(PIConID);
			PI_TranslateError(iError, szMsg, 1024);
			sprintf(szMsg,"Writing segment %i to wave table\n",i);
			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n"); 
			return 0;
		}
		if (i==0) iAppendWave = 2;
	}
	
	// Write last plateau for final image
	iNumberOfWavePoints = (int)(TIllumination /(TControl*WaveGeneratorRate[3]));
	if (pdWavePoints)
		free(pdWavePoints);
	
	pdWavePoints = (double *)malloc(iNumberOfWavePoints*sizeof(double));
	for (i=0;i<iNumberOfWavePoints;i++) pdWavePoints[i] = zend;
				   
	if (!PI_WAV_PNT (PIConID, zWaveGenId, 0, iNumberOfWavePoints, iAppendWave, pdWavePoints )){
		iError = PI_GetError(PIConID);
		PI_TranslateError(iError, szMsg, 1024);
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error writing last segment to wave table:\n"); 
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
		return 0;
	}
	free(pdWavePoints);	  
	//
	// Read waveform back
	nwavepoints = nzsteps*iSegmentLength + iNumberOfWavePoints;
      	SetCtrlVal(hE712pnl, E712_PNL_NWGVAL, nwavepoints);
	
	// read data back
	pdWavePoints = (double *)calloc(nwavepoints,sizeof(double));
	if (PI_qGWD_SYNC (PIConID, zWaveGenId, 1, nwavepoints, pdWavePoints ) ){ // Plot data
		DeleteGraphPlot (hE712pnl, E712_PNL_PI_GRPH, -1, VAL_IMMEDIATE_DRAW); 
		hPlot = PlotY (hE712pnl, E712_PNL_PI_GRPH, pdWavePoints,nwavepoints, VAL_DOUBLE, VAL_CONNECTED_POINTS, VAL_SOLID_SQUARE, VAL_SOLID, 1,VAL_RED); 
		SetPlotAttribute (hE712pnl, E712_PNL_PI_GRPH, hPlot, ATTR_PLOT_LG_TEXT,"z-Waveform"); 
	}
	 else {
		PI_TranslateError(iError, szMsg, 1024);
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error reading back the wave table data:\n"); 
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
		return 0;
	}
	//free(pdWavePoints);  
	
	// Connect Wave Generator to Table
	if (!PI_WSL (PIConID,  &zWaveGenId,  &zWaveGenId, 1) ){
		iError = PI_GetError(PIConID);
		PI_TranslateError(iError, szMsg, 1024);
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error connecting wave generator of z-axis to wave table:\n"); 
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
		return 0;
	} 
	
	// Set number of cycles to 1
	nWGCycles=1; 
	if (!PI_WGC (PIConID,&zWaveGenId, &nWGCycles,1) ){
		iError = PI_GetError(PIConID);
		PI_TranslateError(iError, szMsg, 1024);
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Errorsetting wave generator cycles to 1:\n"); 
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
		return 0;
	} 
		
	// Configure output trigger
	 if (!PI_TWC(PIConID)){ // Sets all values to low
		iError = PI_GetError(PIConID);
		PI_TranslateError(iError, szMsg, 1024);
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error clearing the trigger points:\n"); 
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
		return 0;
	 }
	 else {
		//	nTrigVals = (nIllumination)*(nzsteps + 1); // Output only at illumination of CCD Camera, typical nIllumination=140, nzsteps = 6, nTrigVals = 980
		nTrigVals = nwavepoints;
		TrigChannelIds = (int *)calloc(nTrigVals,sizeof(int));
		TrigPointNumber = (int *)calloc(nTrigVals,sizeof(int));
		TrigVal = (int *)calloc(nTrigVals,sizeof(int));
		
		for (i=0;i<nTrigVals;i++){ 
			TrigChannelIds[i] = 1;						// Output Line 1
			TrigVal[i] = 1;
			TrigPointNumber[i] = i+1;
		}
	
		k=0; /*
		for (i=0;i<nzsteps+1;i++){
			for (k=0;k< nIllumination;k++){
				TrigPointNumber[i*nIllumination + k] = i*iSegmentLength + k + 1;  // typical: iSegmentLength=568
			}
			
		}   */
		// Warning: Input of Controller for commands is limited to max_sent values
		nsent = (int)floor((double)(nTrigVals)/max_sent);
		for (i=0;i<nsent;i++){
				if (!PI_TWS(PIConID, &TrigChannelIds[i*max_sent], &TrigPointNumber[i*max_sent], &TrigVal[i*max_sent], max_sent)){
				iError = PI_GetError(PIConID);																	// iError = 24: Incorrect number of parameters
				PI_TranslateError(iError, szMsg, 1024);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error defining the trigger points:\n"); 
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n");      
				return 0;
			}
		}
		// Send last part
		nsent_last = nTrigVals-nsent*max_sent;
		
		if (nsent_last >0){
			if (!PI_TWS(PIConID, &TrigChannelIds[nsent*max_sent], &TrigPointNumber[nsent*max_sent], &TrigVal[nsent*max_sent], nsent_last)){
				iError = PI_GetError(PIConID);																	// iError = 24: Incorrect number of parameters
				PI_TranslateError(iError, szMsg, 1024);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error defining the trigger points:\n"); 
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n");      
				return 0;
			}
		}  
	
		free(TrigChannelIds);
		free(TrigVal);
	
		nTrigParameter = 2;											// used are parameter 2: axis and 3: mode; 7: polarity, set to 1
		TrigChannelIds =(int *)calloc(nTrigParameter, sizeof(int));  
		TrigParameter  =(int *)calloc(nTrigParameter, sizeof(int));  
		TrigParameterVal=(double *)calloc(nTrigParameter, sizeof(double));
		
		for (i=0;i < nTrigParameter;i++) TrigChannelIds[i] = 1; // Use Output 1
		TrigParameter[0] = 2;
		TrigParameter[1] = 3;
		TrigParameterVal[0] = 4;	// z-axis
		TrigParameterVal[1] = 9;	// Generator Pulse Trigger mode
		
		if ( !PI_CTO (PIConID, TrigChannelIds, TrigParameter, TrigParameterVal, nTrigParameter)  ) {
			iError = PI_GetError(PIConID);
			PI_TranslateError(iError, szMsg, 1024);
			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error setting the trigger options:\n"); 
			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
			free(TrigChannelIds);
			free(TrigParameter);
			free(TrigParameterVal);
			return 0;
		}
		else {
			free(TrigParameter);
			free(TrigParameterVal);
		}
	 } // else TWC 
	 // Read trigger back
	 if (!PI_qTWS(PIConID, &TrigChannelIds[0], 1, 1, nwavepoints, &pdTriggerVals,GCSHeader, 1024)){
		 iError = PI_GetError(PIConID);
		PI_TranslateError(iError, szMsg, 1024);
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error raeding the trigger points back:\n"); 
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
	 }
	 else{
		 do {
			 i = PI_GetAsyncBufferIndex (PIConID);
		 } while (i < nwavepoints);
		 hPlot = PlotY (hE712pnl, E712_PNL_PI_GRPH, pdTriggerVals, nwavepoints, VAL_DOUBLE, VAL_VERTICAL_BAR, VAL_SOLID_SQUARE, VAL_SOLID, 1, VAL_YELLOW);
		 SetPlotAttribute (hE712pnl, E712_PNL_PI_GRPH, hPlot, ATTR_PLOT_LG_TEXT,"Trigger Position"); 
	 } 
	 free(TrigChannelIds);
	/* For debug purposes
	fp=fopen("TrigTest.txt","w");
	 for (i=0;i<nwavenumber;i++)
		 fprintf(fp,"%d\t%lf\n",TrigPointNumber[i],pdTriggerVals[i]);
	 fflush(fp);
	 Delay(0.1);
	 fclose(fp);
	*/
	 free(TrigPointNumber);
	
	return nwavepoints;		
}
int CVICALLBACK configure_wave_generator (int panel, int control, int event, void *callbackData, int eventData1, int eventData2) {
	
	double zstart, zstep;
	unsigned short  nzsteps=0;
	int WG_StartModus=0;
	
	switch (event){
		case EVENT_COMMIT:
			WaveGeneratorRate[3] = 1;							//z-axis 
			GetCtrlVal(hE712pnl, E712_PNL_NZSTART,&zstart);
			GetCtrlVal(hE712pnl, E712_PNL_NDZ,&zstep); 
			GetCtrlVal(hE712pnl, E712_PNL_NNZSTEPS, &nzsteps);
			
			GetCtrlVal(hE712pnl, E712_PNL_NILLUTIME, &TIllumination);
			GetCtrlVal(hE712pnl, E712_PNL_NTRANSFERTIME,&TFrameTransfer);
			
			//Stop wave generator
			if (!PI_WGO (PIConID,  &zWaveGenId,&WG_StartModus, 1 )){
					iError = PI_GetError(PIConID);
					PI_TranslateError(iError, szMsg, 1024);
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Wave generator of z-axis did not stop:\n"); 
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
					return 0;
				}
			
			nwavepoints = generate_z_waveform_and_triggers( TIllumination,  TFrameTransfer,  TControl, zstart, zstep,nzsteps);
			if (nwavepoints ==0)
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Setup of wave generator failed \n");
			else
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Wave generator configured \n"); 	
				
		break;
	}
	return 0;
}

int CVICALLBACK start_wave_generator (int panel, int control, int event,void *callbackData, int eventData1, int eventData2)
{
	// Data recorder
	int RecIds[6]={1,2,3,4,5,6}, RecOpt[6]={2,2,2,2,2,2},qRecOpt[6];  // 2 aktuelle Werte der Achse 
	//int RecBufSize=nDataRecChan, RecOptSize=nDataRecChan ;
	char SrcIds[]="1\n2\n3\n4\n5\n6\n"; 			// Achsen 1 bis 6 werden den Tables 1-6 zugeordnet
	int DataRecChanSelect[nDataRecChan]={1,1,1,1,1,1};		// Which channels to read
	//int TrigSrc[3]={4,4,4};	//
	//char DRC_TrigVal[]="0\n0\n0\n";	// dummy values if trig source = 4: function cal of DRT triggers start; Trigger Channel if
	//BOOL res=FALSE;
	char qSrcIds[1024];
	int max_recorded=0,nold=0;// nrecorded[nDataRecChan] ={0}, min_recorded=0;						// Number of values to record
	int NfRecTables = 6;
	int i=0,k=0;									// loop variables
	//char HDRText[1024];
	char GCSHeader[1024];
	double **RecData, *data,**PulseData=NULL;
	int hPlot=0;
	double dPIPosZ=0;
	int use_start_trigger=0;
	BOOL is_wave_gen_running = FALSE;
	double TIllumination, TFrameTransfer;
	
	switch (event)  {
		case EVENT_COMMIT:
			if (nwavepoints ==0) {
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Setup wave generator first ! \n"); 
				return 0;
			}
			// get arameters of the wave
			GetCtrlVal(hE712pnl, E712_PNL_NZSTART, &dPIPosZ);
			GetCtrlVal(hE712pnl, E712_PNL_WG_TRIG_SELECT, &use_start_trigger);
			GetCtrlVal(hE712pnl, E712_PNL_NNZSTEPS,(unsigned short *) &iNbOfSteps);
			GetCtrlVal(hE712pnl, E712_PNL_NILLUTIME,&TIllumination);								// in msec
			GetCtrlVal(hE712pnl, E712_PNL_NTRANSFERTIME,&TFrameTransfer); 							// in msec
			// Adjust Counter parameters
			DAQmxErrChk (DAQmxSetCOPulseHighTicks(taskHandleCTR0,"ShutterCCD", TIllumination*100));	 //100 KHz clock, 100 pulses per msec	
			DAQmxErrChk (DAQmxSetCOPulseLowTicks(taskHandleCTR0,"ShutterCCD", TFrameTransfer*100));
			// Set Properties of 2nd Diagramm
			SetCtrlAttribute (hE712pnl, E712_PNL_PI_GRPH2, ATTR_XNAME, "Time in msec");
			SetCtrlAttribute (hE712pnl, E712_PNL_PI_GRPH2, ATTR_YNAME, "Position in um");
			SetCtrlAttribute (hE712pnl, E712_PNL_PI_GRPH2, ATTR_XMAP_MODE, VAL_LINEAR);
			SetCtrlAttribute (hE712pnl, E712_PNL_PI_GRPH2, ATTR_YMAP_MODE, VAL_LINEAR);
			// Acquire data arrays 
			data = (double *)malloc(sizeof(double));
			RecData = (double **)malloc(NfRecTables*sizeof(double *));
			for (i=0;i<NfRecTables;i++)
				RecData[i]= (double *)calloc(nwavepoints,sizeof(double));
		
			//setup data recorder
			if( PI_DRC (PIConID, RecIds, SrcIds, RecOpt)){
				if (PI_qDRC (PIConID , RecIds, qSrcIds, qRecOpt, sizeof( qSrcIds),NfRecTables)){
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Data recorder configured for axis:\n");
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX, qSrcIds);
				}
				else {
					iError = PI_GetError(PIConID);
					PI_TranslateError(iError, szMsg, 1024);
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error reading the Data recorder configuration\n");   
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n"); 
					return 0;
				}
			}
			else {
				iError = PI_GetError(PIConID);
				PI_TranslateError(iError, szMsg, 1024);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Error during setup of the data recorder\n");   
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n");  
				return 0;
			}
			// Restart recording when wave generator starts
			PI_WGR(PIConID);
			Delay(0.1);
			
			// Test whether recorder tables are empty
			PI_qDRL (PIConID,  RecIds, RecOpt,NfRecTables);
			max_recorded = RecOpt[NfRecTables-1];
			if (max_recorded != 0)
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Values left in the recorder tables !\n");
			
			if (!use_start_trigger)
				WG_StartModus = 1;			// 1 immediate start, 0 stop, 2: start by trigger, Signal at In1; In2 ist a start /stop trigger !
			else {
				WG_StartModus = 2;
				//**** Stop synchronisation signals NI Tasks
				DAQmxStopTask(taskHandleCTR0); 
				DAQmxStopTask(taskHandleCTR1); 
				DAQmxStopTask(taskHandleCTR2);
				
				Sleep(10);
				if( DAQmxFailed(iError) )	{ 
					DAQmxGetExtendedErrorInfo(szErrBuff,2048);
					Fmt(szMsg,"%s<%s%s%s","DAQmx Error:",szErrBuff, "\n");
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
				}
				// Reset digital Output
				ucDigitalOutputState = 1;
				DAQmxErrChk (DAQmxWriteDigitalLines(taskHandleDigitalOutput, 1, 1, 10.0, DAQmx_Val_GroupByChannel, &ucDigitalOutputState, &iNbSamplesWrittenSuccessfully, 0)); 
				DAQmxErrChk (DAQmxTaskControl(taskHandleCTR0, DAQmx_Val_Task_Commit));
				DAQmxErrChk (DAQmxTaskControl(taskHandleCTR1, DAQmx_Val_Task_Commit));
				DAQmxErrChk (DAQmxTaskControl(taskHandleCTR2, DAQmx_Val_Task_Commit));
				// unregister interrupt function to stop data acquisition reliable
				DAQmxErrChk (DAQmxRegisterSignalEvent(taskHandleCTR0, DAQmx_Val_CounterOutputEvent, 0, NULL, NULL)); 
			
			}
			
			// Start Wave Generator
			if (!PI_WGO (PIConID,  &zWaveGenId,&WG_StartModus, 1 )){
				iError = PI_GetError(PIConID);
				PI_TranslateError(iError, szMsg, 1024);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Wave generator of z-axis did not start:\n"); 
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
				return 0;
			}
			 if (use_start_trigger){
				iTestAcqData = 0;
				 ucDigitalOutputState = 1;
				 // register interrupt function to stop data acquisition reliable
				DAQmxErrChk (DAQmxRegisterSignalEvent(taskHandleCTR0, DAQmx_Val_CounterOutputEvent, 0, acq_data, NULL)); 
				Delay(0.01);
				DAQmxErrChk (DAQmxWriteDigitalLines(taskHandleDigitalOutput, 1, 1, 10.0, DAQmx_Val_GroupByChannel, &ucDigitalOutputState, &iNbSamplesWrittenSuccessfully, 0));
				DAQmxErrChk (DAQmxStartTask(taskHandleCTR0));
				DAQmxErrChk (DAQmxStartTask(taskHandleCTR1));
				DAQmxErrChk (DAQmxStartTask(taskHandleCTR2));
				 
				//Start pulse gneration 
				ucDigitalOutputState = 0;
				DAQmxErrChk (DAQmxWriteDigitalLines(taskHandleDigitalOutput, 1, 1, 10.0, DAQmx_Val_GroupByChannel, &ucDigitalOutputState, &iNbSamplesWrittenSuccessfully, 0));
			 }
			do { // until wave generator starts
				Delay(0.1); 
				PI_IsGeneratorRunning(PIConID,  &zWaveGenId, &is_wave_gen_running, 1);
			 } while (!is_wave_gen_running);
			
			if (WG_StartModus == 2)  {
				do { // until wave generator stops
					PI_IsGeneratorRunning(PIConID,  &zWaveGenId, &is_wave_gen_running, 1);
					//DAQmxErrChk (DAQmxGetReadAttribute (taskHandleCTR2, DAQmx_Read_AvailSampPerChan, &iNbCounted, 1)); 
				 } while (is_wave_gen_running || (iTestAcqData<(iNbOfSteps+1)) );
			}
			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Wave generator: Motion complete\n"); 
			// Start asynchronous read
			if (PI_qDRR (PIConID,RecIds,NfRecTables, 1, nwavepoints, &data, GCSHeader,1024)){
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Data recorder: read data\n"); 
				do {
					//Delay(0.001);
					PI_qDRL (PIConID,  RecIds, RecOpt,NfRecTables);
					max_recorded = RecOpt[NfRecTables-1];
					
					SetCtrlVal(hE712pnl,E712_PNL_NWGVAL, max_recorded);
					ProcessSystemEvents();
					if (max_recorded > nwavepoints)
						 max_recorded = nwavepoints;
					for (i=nold;i<max_recorded;i++){
						for (k=0;k<NfRecTables;k++){
							RecData[k][i]=data[i*NfRecTables+k];
						}
					}
					nold = max_recorded;
				} while (max_recorded < nwavepoints);
				WG_StartModus = 0;			// 1 immediate start, 0 stop, 2: start by trigger
				// Stop Wave Generator
				if (!PI_WGO (PIConID,  &zWaveGenId,&WG_StartModus, 1 )){
					iError = PI_GetError(PIConID);
					PI_TranslateError(iError, szMsg, 1024);
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Wave generator of z-axis did not stop:\n"); 
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
					return 0;
				}
				else{
					SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Data recorder data: data transfered\n");
				}
				// Daten gelesen
				SetCtrlVal(hE712pnl, E712_PNL_NDRVAL,nwavepoints);
				// Calculate difference between real z-motion and desired z-values
				if (!use_start_trigger){
				for (i=0;i<nwavepoints;i++)
					RecData[3][i]-= pdWavePoints[i];
				}
				
				PI_WGR(PIConID);
				
				// Move stage in start position 
				PI_MOV(PIConID,"4",&dPIPosZ); 
				
				// Plot data
				DeleteGraphPlot (hE712pnl, E712_PNL_PI_GRPH, -1, VAL_IMMEDIATE_DRAW);
				DeleteGraphPlot (hE712pnl, E712_PNL_PI_GRPH2, -1, VAL_IMMEDIATE_DRAW);
				if (!use_start_trigger){
					k=0;
					for (i=0;i<nDataRecChan;i++){
						if (DataRecChanSelect[i] ){
							if (i==3) {// z-axis
								hPlot=PlotY (hE712pnl, E712_PNL_PI_GRPH2, RecData[k],nwavepoints, VAL_DOUBLE, VAL_CONNECTED_POINTS, VAL_SOLID_SQUARE, VAL_SOLID, 1, pcolor[i]);
								SetPlotAttribute (hE712pnl, E712_PNL_PI_GRPH2, hPlot, ATTR_PLOT_LG_TEXT, legends[i]); 
							}
							else {
								hPlot=PlotY (hE712pnl, E712_PNL_PI_GRPH, RecData[k],nwavepoints, VAL_DOUBLE, VAL_CONNECTED_POINTS, VAL_SOLID_SQUARE, VAL_SOLID, 1, pcolor[i]);
								SetPlotAttribute (hE712pnl, E712_PNL_PI_GRPH, hPlot, ATTR_PLOT_LG_TEXT, legends[i]);
							}
							k++;
						}
					}
				}//use_start_trigger
				else { // select points that were acquireed during the time when CTR0 is high (illumination of CCD camera in later application)
					DAQmxErrChk (DAQmxGetReadAttribute (taskHandleCTR2, DAQmx_Read_AvailSampPerChan, &iNbCounted, 1));
					if (iNbCounted == 0) {
						Fmt(szMsg,"%s<%s","Zero values in the counter\n");
						SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg); 
						return 0;
					}
					else {
						piIndexRecordedByCTR2 = (uInt32 *)calloc(iNbCounted,sizeof(uInt32));
						DAQmxErrChk (DAQmxReadCounterU32(taskHandleCTR2, iNbCounted, 100.0, piIndexRecordedByCTR2, iNbCounted, &iTestNbRead, NULL));
						DAQmxErrChk (DAQmxStopTask (taskHandleCTR2)); 
					}
					piLastTriggerPulse = (int *) calloc(iNbOfSteps+2,sizeof(int));
					piFirstTriggerPulse = (int *) calloc(iNbOfSteps+2,sizeof(int));
					piNTriggerPulse		= (int *) calloc(iNbOfSteps+2,sizeof(int));

					// Determine number of pulse that differ
					nPulseCounted = 0;
					for (ii=1; ii<iNbCounted; ii++){
						if (piIndexRecordedByCTR2[ii] != piIndexRecordedByCTR2[ii-1]) nPulseCounted++;
					}
					
					// Select the indices that differ
					iWaveTableIndex = (int*) calloc(nPulseCounted,sizeof(int));
					kk=0;
					for (ii=1; ii<iNbCounted; ii++){
							if (piIndexRecordedByCTR2[ii] != piIndexRecordedByCTR2[ii-1]){
								iWaveTableIndex[kk] = piIndexRecordedByCTR2[ii];
								kk++;
							}
					}
					
					PulseData = (double **) calloc (NfRecTables,sizeof(double *));
					for (ii=0;ii<NfRecTables;ii++)
						PulseData[ii] = (double *) calloc (nPulseCounted,sizeof(double)); 
				
					// iWaveTableIndex contains all indices of counted pulses during illumination
					// Determine 
					kk=0;
					piFirstTriggerPulse[0] = iWaveTableIndex[0];
					for (ii=1; ii < nPulseCounted-1; ii++){  
						if  (iWaveTableIndex[ii] - iWaveTableIndex[ii-1] >2 ) {	// next illumination period
							piLastTriggerPulse[kk] = iWaveTableIndex[ii-1];			//  number of last triggerr value 
							piFirstTriggerPulse[kk+1] = iWaveTableIndex[ii];		// index of first trigger value	
								piNTriggerPulse[kk] = piLastTriggerPulse[kk] - piFirstTriggerPulse[kk] ;	
							kk++;
						}
					}
					piLastTriggerPulse[kk] = iWaveTableIndex[nPulseCounted-2];
					piNTriggerPulse[kk] = 	piLastTriggerPulse[kk] - piFirstTriggerPulse[kk] ;
					
					if (kk != (iNbOfSteps)){
						SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Not enough steps in counter data detected\n");
						return 0;
					}
					
					// Calculate averages
					xavgs = (double *)calloc(iNbOfSteps+1,sizeof(double));
					yavgs = (double *)calloc(iNbOfSteps+1,sizeof(double));
					zavgs = (double *)calloc(iNbOfSteps+1,sizeof(double));
		
					kk=0;
					for (ii = 0; ii<(iNbOfSteps+1); ii++){
						StdDev (&RecData[0][piFirstTriggerPulse[ii]],piNTriggerPulse[ii], &dAvgX, &dVarzX );
						StdDev (&RecData[1][piFirstTriggerPulse[ii]],piNTriggerPulse[ii], &dAvgY, &dVarzY ); 
						StdDev (&RecData[3][piFirstTriggerPulse[ii]],piNTriggerPulse[ii], &dAvgZ, &dVarzZ ); 
						xavgs[ii] = dAvgX;
						yavgs[ii] = dAvgY; 
						zavgs[ii] = dAvgZ; 
			
						Fmt(szMsg,"%s<%s%d%s%f%s%f%s","Step: ",ii,":  X-POSITION :",1000*dAvgX," +/- : ", 1000*dVarzX, " nm\n");
						SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
						Fmt(szMsg,"%s<%s%f%s%f%s","                    Y-POSITION : ",1000*dAvgY," >  +/-  ", 1000*dVarzY, "nm\n");
						SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
						Fmt(szMsg,"%s<%s%f%s%f%s","                    Z-POSITION : ",1000*dAvgZ,"  +/-  ", 1000*dVarzZ, "nm\n");
						SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
					} 
					// Plot deviations
					// Substract nominal values from z-data
					if (use_start_trigger){
					for (i=0;i<nwavepoints;i++)
						RecData[3][i]-= pdWavePoints[i];
					}
					// Write data recorded during the illumination pulse in arrays
					for (ii=0;ii< nPulseCounted-1;ii++){
						 for (kk=0;kk< NfRecTables;kk++) {
							 PulseData[kk][ii] = RecData[kk][iWaveTableIndex[ii]-1];
						 }
					}
					k=0;
					for (i=0;i<nDataRecChan;i++){
						if (DataRecChanSelect[i] ){
							if (i==3) {// z-axis
								hPlot=PlotY (hE712pnl, E712_PNL_PI_GRPH2, PulseData[k],nPulseCounted, VAL_DOUBLE, VAL_CONNECTED_POINTS, VAL_SOLID_SQUARE, VAL_SOLID, 1, pcolor[i]);
								SetPlotAttribute (hE712pnl, E712_PNL_PI_GRPH2, hPlot, ATTR_PLOT_LG_TEXT, legends[i]); 
							}
							else {
								hPlot=PlotY (hE712pnl, E712_PNL_PI_GRPH, PulseData[k],nPulseCounted, VAL_DOUBLE, VAL_CONNECTED_POINTS, VAL_SOLID_SQUARE, VAL_SOLID, 1, pcolor[i]);
								SetPlotAttribute (hE712pnl, E712_PNL_PI_GRPH, hPlot, ATTR_PLOT_LG_TEXT, legends[i]);
							}
							k++;
						}
					}// for
		
				}
			}
			else{
				iError = PI_GetError(PIConID);
				PI_TranslateError(iError, szMsg, 1024);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Asynchrous read did not start:\n");   
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
				SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"\n"); 
				return 0;
			}

			SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,"Ready\n");
			for (i=0;i<NfRecTables;i++)
				free(RecData[i]);
			free(RecData);
			if (use_start_trigger){
				free(piLastTriggerPulse) ;
				free(piFirstTriggerPulse);
				free(piNTriggerPulse);
				for (i=0;i<NfRecTables;i++)
					free(PulseData[i]);
				free(PulseData);
				free(piIndexRecordedByCTR2);
				free(	iWaveTableIndex);
			}
		break;
	}
	ErrorDAQmx:
	if( DAQmxFailed(iError) )	{
		DAQmxGetExtendedErrorInfo(szErrBuff,2048);
		Fmt(szMsg,"%s<%s%s%s","DAQmx Error:",szErrBuff, "\n");
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
	}
	return 0;
}

// Interrupt function
int32 CVICALLBACK acq_data (TaskHandle taskHandle, int32 signalID, void *callbackData){
	
	//**** uses value returned by PI_Stage_WaveGenarator_Steps()
	//iNbOfPulsesTotal = n2record;;
	//**** (iTestAcqData == 0) >> First Time entering the function acq_data() => start measurement

	if (iTestAcqData == 0) {  
		iTestAcqData++;
		// Trigger a pulse for PI-stage and increasing the priority of the Thread
		SetThreadPriority(GetCurrentThread(),THREAD_PRIORITY_TIME_CRITICAL);
		//DAQmxErrChk (DAQmxStartTask(taskHandleCTR2));
		// Start data acquisition
		ucDigitalOutputState = 1;
		DAQmxErrChk (DAQmxWriteDigitalLines(taskHandleDigitalOutput, 1, 1, 10.0, DAQmx_Val_GroupByChannel, &ucDigitalOutputState, &iNbSamplesWrittenSuccessfully, 0));  
		//**** Starts grabbing (iNbOfSteps+2) frames
		//MdigProcess(MilCamera, MilSeqBufFocus,iNbOfSteps+1,M_SEQUENCE+M_COUNT(iNbOfSteps+1),M_SYNCHRONOUS, M_NULL, M_NULL);
		return 0;
	}
	//**** acq_data() is entered at each low and high edge of the counter taskHandleCTR0
	else if ((iTestAcqData >= 1) && (iTestAcqData <(2*iNbOfSteps+1))){ 
		iTestAcqData++; 
		return 0; 
	}
	else {  // Data ready
		DAQmxErrChk (DAQmxStopTask (taskHandleCTR0));
		//DAQmxErrChk (DAQmxRegisterSignalEvent(taskHandleCTR0, DAQmx_Val_CounterOutputEvent, 0, NULL, NULL)); 
		DAQmxErrChk (DAQmxStopTask (taskHandleCTR1));
		//DAQmxErrChk (DAQmxGetReadAttribute (taskHandleCTR2, DAQmx_Read_AvailSampPerChan, &iNbCounted, 1));
		//DAQmxErrChk (DAQmxStopTask (taskHandleCTR2));
		SetThreadPriority(GetCurrentThread(),THREAD_PRIORITY_NORMAL); 
	}
		ErrorDAQmx:
	if( DAQmxFailed(iError) )	{
		DAQmxGetExtendedErrorInfo(szErrBuff,2048);
		Fmt(szMsg,"%s<%s%s%s","DAQmx Error:",szErrBuff, "\n");
		SetCtrlVal(hE712pnl, E712_PNL_PIMSGBOX,szMsg);
	}
	return 0;
}
		   

int CVICALLBACK calc_DR_FFT (int panel, int control, int event,	 void *callbackData, int eventData1, int eventData2)
{
	switch (event) {
		case EVENT_COMMIT:

		break;
	}
	return 0;
}
