The F-712 systems provide routines for fast alignment of one or more senders and receivers. The objective of the routines is to align each sender and receiver so that the maximum intensity of the emitted signal is measured on the receiver side.

The following types of fast alignment routines are provided:
•	“Area scan”: Spiral or raster scan to find the position of the global intensity maximum of the measured signal
•	“Gradient search”: Circular scan with gradient formation to find the maximum intensity value of the measured signal
Typically, the end position of an area scan routine is used as the start position for a gradient search routine.
The maximum number of routines is identical to the number of motion axes that are present in the system (E-712 controller only).
Multiple gradient search routines can run synchronously for the axes on both the sender and receiver side (E-712 controller only).
Application examples:
Sender and receiver are optical fibers. During the alignment of sender and receiver in axes x, y and z, the power of the optical signal (light) is measured on the receiver side with a power meter. The power meter converts the optical power into an analog signal. Goal of the alignment routines is to align sender and receiver so that the maximum optical power is measured on the receiver side. 
Multiple couplings (for example, of the input and output of a waveguide device) have to be optimized (Only with E-712 controller). In this case, gradient search routines for the couplings can be performed simultaneously, ensuring a global optimization, even if the couplings interact. Similarly, for lensed couplings a Z gradient search may also be performed at the same time.

This sample application shows how how PI's programminge libraries can be used for fast routine tasks.
The sample application is provided “as is” and with no guarantee of working properly.

The code is open source and can be adjusted to customer’s needs without asking PI for permission.
