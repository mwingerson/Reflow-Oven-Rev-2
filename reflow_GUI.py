#!/usr/bin/python

# Reflow Oven GUI

import Tkinter 
from serial.tools import list_ports
import matplotlib as mpl
from numpy import arange, sin, pi, cos
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import numpy as np
import threading
import time
import serial
import Queue

class serial_worker(threading.Thread):
	ser = None
	continue_program = True
	connected = False
	inbox = Queue.Queue()
	outbox = Queue.Queue()

	def __init__(self):
		threading.Thread.__init__(self)

	def connect(self, port):
		self.ser = serial.Serial(port, 115200)
		self.connected = True

	def disconnect(self):
		self.connected = False
		self.ser.close()

	def run(self):
		print "Starting Serial printer"

		while(self.continue_program):			
			if(self.connected):
				if(not self.outbox.empty()):
					buf = self.outbox.get()
					buf = buf + '\r'
					print "Outbox: |%s|" % buf.strip()
					self.ser.write(buf)
					# self.ser.write(self.outbox.get())

				buf = self.ser.readline()
				if len(buf) > 0:
					print "%s" % buf
					self.inbox.put(buf.strip())
					time.sleep(0.1)
		if self.ser != None:
			self.ser.close()
		return

	def close(self):
		self.continue_program = False
		return

class reflow_GUI(Tkinter.Tk):
	trimmed_port_list = []
	selected_port = None
	temp_var = None
	ser = None

	def __init__(self,parent):
		Tkinter.Tk.__init__(self,parent)
		self.parent = parent
		self.ser = serial_worker()
		self.ser.start()

		self.initialize()

	def	stop_prog(self):
		# print "stopping program"

		if self.ser != None:
			self.ser.close()
			self.ser.join()

		# print "Returning from stop"
		return

	def connect_button_handler(self):
		self.selected_port = str(self.temp_var.get()).split(' ')[0]
		print "Selected port: %s" % self.selected_port
	
		if self.ser.connected:
			self.ser.disconnect()

		self.ser.connect(self.selected_port)

	def update_button_handler(self):
		# print "in update"
		buf = ("update " + 
				str(self.updatePreheatP.get()) + " " + 
				str(self.updatePreheatI.get()) + " " + 
				str(self.updatePreheatD.get()) + " " + 
			   	str(self.updateSoakP.get()) + " " + 
			   	str(self.updateSoakI.get()) + " " + 
			   	str(self.updateSoakD.get()) + " " + 
			   	str(self.updateReflowP.get()) + " " + 
			   	str(self.updateReflowI.get()) + " " + 
			   	str(self.updateReflowD.get()) + " " + 
			   	str(self.updateCoolP.get()) + " " + 
			   	str(self.updateCoolI.get()) + " " + 
			   	str(self.updateCoolD.get()) + " " + 

			   	str(self.updatePreheatTemp.get()) + " " + 
			   	str(self.updateSoakMin.get()) + " " + 
			   	str(self.updateSoakMax.get()) + " " + 
			   	str(self.updateSoakTime.get()) + " " + 
			   	str(self.updateReflowMax.get())) 

		# self.updatePreheatTemp = Tkinter.DoubleVar(self, self.preheat_temp.get())
		# self.updateSoakMin = Tkinter.DoubleVar(self, self.soak_min.get())
		# self.updateSoakMax = Tkinter.DoubleVar(self, self.soak_max.get())
		# self.updateSoakTime = Tkinter.DoubleVar(self, self.soak_time.get())
		# self.updateReflowMax = Tkinter.DoubleVar(self, self.reflow_max.get())

		# print "buf: %s" % buf
		self.ser.outbox.put(buf)

	def start_button_handler(self):
		self.ser.outbox.put("start");

	def stop_button_handler(self):
		self.ser.outbox.put("stop");

	def hold_preheat_handler(self):
		self.ser.outbox.put("hold_preheat");

	def hold_soak_handler(self):
		self.ser.outbox.put("hold_soak");

	def hold_reflow_handler(self):
		self.ser.outbox.put("hold_reflow");

	def get_params_buttom_handler(self):
		self.ser.outbox.put("get_param");

	def initialize(self):
		self.obs_temp_data = list()
		self.exp_temp_data = list()

		self.preheat_P = Tkinter.DoubleVar(self, 1.0)
		self.preheat_I = Tkinter.DoubleVar(self, 1.0)
		self.preheat_D = Tkinter.DoubleVar(self, 1.0)
		self.soak_P = Tkinter.DoubleVar(self, 1.0)
		self.soak_I = Tkinter.DoubleVar(self, 1.0)
		self.soak_D = Tkinter.DoubleVar(self, 1.0)
		self.reflow_P = Tkinter.DoubleVar(self, 1.0)
		self.reflow_I = Tkinter.DoubleVar(self, 1.0)
		self.reflow_D = Tkinter.DoubleVar(self, 1.0)
		self.cool_P = Tkinter.DoubleVar(self, 1.0)
		self.cool_I = Tkinter.DoubleVar(self, 1.0)
		self.cool_D = Tkinter.DoubleVar(self, 1.0)

		self.preheat_temp = Tkinter.DoubleVar(self, 50.0)
		self.soak_min = Tkinter.DoubleVar(self, 140.0)
		self.soak_max = Tkinter.DoubleVar(self, 160.0)
		self.soak_time = Tkinter.DoubleVar(self, 75.0)
		self.reflow_max = Tkinter.DoubleVar(self, 215.0)

		self.grid()

		# Create list of trimmed com ports
		full_port_list = list_ports.comports()
	
		for temp in full_port_list:
			self.trimmed_port_list.append(temp[0])

		# self.geometry("750x200+300+300")

		# Code to add widgets will go here...

		self.temp_var = Tkinter.StringVar(self)
		self.temp_var.set(self.trimmed_port_list[0])

		# Column 0
		self.optMenu = Tkinter.OptionMenu(self, self.temp_var, *self.trimmed_port_list)
		self.optMenu.grid(column=0, row=0, columnspan=2)

		self.parameterHeader = Tkinter.Label(self, anchor="w",fg="black", text="Parameter", font="bold")
		self.parameterHeader.grid(column=0, row=1)

		self.preheatPLabel = Tkinter.Label(self, anchor="w",fg="black", text="Preheat P")
		self.preheatPLabel.grid(column=0, row=2)

		self.preheatILabel = Tkinter.Label(self, anchor="w",fg="black", text="Preheat I")
		self.preheatILabel.grid(column=0, row=3)

		self.preheatDLabel = Tkinter.Label(self, anchor="w",fg="black", text="Preheat D")
		self.preheatDLabel.grid(column=0, row=4)

		self.soakPLabel = Tkinter.Label(self, anchor="w",fg="black", text="Soak P")
		self.soakPLabel.grid(column=0, row=5)

		self.soakILabel = Tkinter.Label(self, anchor="w",fg="black", text="Soak I")
		self.soakILabel.grid(column=0, row=6)

		self.soakDLabel = Tkinter.Label(self, anchor="w",fg="black", text="Soak D")
		self.soakDLabel.grid(column=0, row=7)

		self.reflowPLabel = Tkinter.Label(self, anchor="w",fg="black", text="Reflow P")
		self.reflowPLabel.grid(column=0, row=8)

		self.reflowILabel = Tkinter.Label(self, anchor="w",fg="black", text="Reflow I")
		self.reflowILabel.grid(column=0, row=9)

		self.reflowDLabel = Tkinter.Label(self, anchor="w",fg="black", text="Reflow D")
		self.reflowDLabel.grid(column=0, row=10)

		self.coolPLabel = Tkinter.Label(self, anchor="w",fg="black", text="Cool P")
		self.coolPLabel.grid(column=0, row=11)

		self.coolILabel = Tkinter.Label(self, anchor="w",fg="black", text="Cool I")
		self.coolILabel.grid(column=0, row=12)

		self.coolDLabel = Tkinter.Label(self, anchor="w",fg="black", text="Cool D")
		self.coolDLabel.grid(column=0, row=13)

		self.preheatTempLabel = Tkinter.Label(self, anchor="w",fg="black", text="Preheat Temp")
		self.preheatTempLabel.grid(column=0, row=14)

		self.soakTempMinLabel = Tkinter.Label(self, anchor="w",fg="black", text="Soak Temp Min")
		self.soakTempMinLabel.grid(column=0, row=15)

		self.soakTempMaxLabel = Tkinter.Label(self, anchor="w",fg="black", text="Soak Temp Max")
		self.soakTempMaxLabel.grid(column=0, row=16)

		self.soakTimeLabel = Tkinter.Label(self, anchor="w",fg="black", text="Soak Time")
		self.soakTimeLabel.grid(column=0, row=17)

		self.reflowMaxLabel = Tkinter.Label(self, anchor="w",fg="black", text="reflow Temp Max")
		self.reflowMaxLabel.grid(column=0, row=18)

		self.updateButton = Tkinter.Button(self, text="Update", command=self.update_button_handler)
		self.updateButton.grid(column=0,row=19, columnspan=1)

		# Column 1
		self.currentHeader = Tkinter.Label(self, anchor="w",fg="black", text="Current", font="bold")
		self.currentHeader.grid(column=1, row=1)

		# self.currentpVal = Tkinter.Label(self, anchor="w",fg="black", text=self.pScalar.get())
		self.preheatPVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.preheat_P)
		self.preheatPVal.grid(column=1, row=2)

		self.preheatIVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.preheat_I)
		self.preheatIVal.grid(column=1, row=3)

		self.preheatDVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.preheat_D)
		self.preheatDVal.grid(column=1, row=4)

		self.soakPVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.soak_P)
		self.soakPVal.grid(column=1, row=5)

		self.soakIVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.soak_I)
		self.soakIVal.grid(column=1, row=6)

		self.soakDVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.soak_D)
		self.soakDVal.grid(column=1, row=7)

		self.reflowPVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.reflow_P)
		self.reflowPVal.grid(column=1, row=8)

		self.reflowIVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.reflow_I)
		self.reflowIVal.grid(column=1, row=9)

		self.reflowDVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.reflow_D)
		self.reflowDVal.grid(column=1, row=10)
		
		self.coolPVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.cool_P)
		self.coolPVal.grid(column=1, row=11)

		self.coolIVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.cool_I)
		self.coolIVal.grid(column=1, row=12)

		self.coolDVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.cool_D)
		self.coolDVal.grid(column=1, row=13)

		self.preheatTempVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.preheat_temp)
		self.preheatTempVal.grid(column=1, row=14)

		self.soakMinVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.soak_min)
		self.soakMinVal.grid(column=1, row=15)
		
		self.soakMaxVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.soak_max)
		self.soakMaxVal.grid(column=1, row=16)

		self.soakTimeVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.soak_time)
		self.soakTimeVal.grid(column=1, row=17)

		self.reflowMaxVal = Tkinter.Label(self, anchor="w",fg="black", textvariable=self.reflow_max)
		self.reflowMaxVal.grid(column=1, row=18)

		self.paramsButton = Tkinter.Button(self, text="Get Params", command=self.get_params_buttom_handler)
		self.paramsButton.grid(column=1,row=19, columnspan=1)

		# Column 2
		self.connect_button = Tkinter.Button(self, text="Connect", command=self.connect_button_handler)
		self.connect_button.grid(column=2,row=0)

		self.updateHeader = Tkinter.Label(self, anchor="w",fg="black", text="Update", font="bold")
		self.updateHeader.grid(column=2, row=1)

		self.updatePreheatP = Tkinter.DoubleVar(self, self.preheat_P.get())
		self.updatePreheatI = Tkinter.DoubleVar(self, self.preheat_I.get())
		self.updatePreheatD = Tkinter.DoubleVar(self, self.preheat_D.get())
		self.updateSoakP = Tkinter.DoubleVar(self, self.soak_P.get())
		self.updateSoakI = Tkinter.DoubleVar(self, self.soak_I.get())
		self.updateSoakD = Tkinter.DoubleVar(self, self.soak_D.get())
		self.updateReflowP = Tkinter.DoubleVar(self, self.reflow_P.get())
		self.updateReflowI = Tkinter.DoubleVar(self, self.reflow_I.get())
		self.updateReflowD = Tkinter.DoubleVar(self, self.reflow_D.get())
		self.updateCoolP = Tkinter.DoubleVar(self, self.cool_P.get())
		self.updateCoolI = Tkinter.DoubleVar(self, self.cool_I.get())
		self.updateCoolD = Tkinter.DoubleVar(self, self.cool_D.get())

		self.updatePreheatTemp = Tkinter.DoubleVar(self, self.preheat_temp.get())
		self.updateSoakMin = Tkinter.DoubleVar(self, self.soak_min.get())
		self.updateSoakMax = Tkinter.DoubleVar(self, self.soak_max.get())
		self.updateSoakTime = Tkinter.DoubleVar(self, self.soak_time.get())
		self.updateReflowMax = Tkinter.DoubleVar(self, self.reflow_max.get())

		self.preheatPEntry = Tkinter.Entry(self, textvariable=self.updatePreheatP)
		self.preheatPEntry.grid(column=2, row=2, sticky='EW')

		self.preheatIEntry = Tkinter.Entry(self, textvariable=self.updatePreheatI)
		self.preheatIEntry.grid(column=2, row=3, sticky='EW')

		self.preheatDEntry = Tkinter.Entry(self, textvariable=self.updatePreheatD)
		self.preheatDEntry.grid(column=2, row=4, sticky='EW')

		self.soakPEntry = Tkinter.Entry(self, textvariable=self.updateSoakP)
		self.soakPEntry.grid(column=2, row=5, sticky='EW')

		self.soakIEntry = Tkinter.Entry(self, textvariable=self.updateSoakI)
		self.soakIEntry.grid(column=2, row=6, sticky='EW')

		self.soakDEntry = Tkinter.Entry(self, textvariable=self.updateSoakD)
		self.soakDEntry.grid(column=2, row=7, sticky='EW')

		self.reflowPEntry = Tkinter.Entry(self, textvariable=self.updateReflowP)
		self.reflowPEntry.grid(column=2, row=8, sticky='EW')

		self.reflowIEntry = Tkinter.Entry(self, textvariable=self.updateReflowI)
		self.reflowIEntry.grid(column=2, row=9, sticky='EW')

		self.reflowDEntry = Tkinter.Entry(self, textvariable=self.updateReflowD)
		self.reflowDEntry.grid(column=2, row=10, sticky='EW')

		self.coolPEntry = Tkinter.Entry(self, textvariable=self.updateCoolP)
		self.coolPEntry.grid(column=2, row=11, sticky='EW')

		self.coolIEntry = Tkinter.Entry(self, textvariable=self.updateCoolI)
		self.coolIEntry.grid(column=2, row=12, sticky='EW')

		self.coolDEntry = Tkinter.Entry(self, textvariable=self.updateCoolD)
		self.coolDEntry.grid(column=2, row=13, sticky='EW')

		self.preheatTempEntry = Tkinter.Entry(self, textvariable=self.updatePreheatTemp)
		self.preheatTempEntry.grid(column=2, row=14, sticky='EW')

		self.soakMinEntry = Tkinter.Entry(self, textvariable=self.updateSoakMin)
		self.soakMinEntry.grid(column=2, row=15, sticky='EW')

		self.soakMaxEntry = Tkinter.Entry(self, textvariable=self.updateSoakMax)
		self.soakMaxEntry.grid(column=2, row=16, sticky='EW')

		self.soakTimeEntry = Tkinter.Entry(self, textvariable=self.updateSoakTime)
		self.soakTimeEntry.grid(column=2, row=17, sticky='EW')

		self.reflowMaxEntry = Tkinter.Entry(self, textvariable=self.updateReflowMax)
		self.reflowMaxEntry.grid(column=2, row=18, sticky='EW')

		# Column 3
		self.Start_button = Tkinter.Button(self, text="Start", background="green", foreground="black", command=self.start_button_handler)
		self.Start_button.grid(column=3,row=0)

		fig_dpi = 100

		self.fig = mpl.figure.Figure(dpi=fig_dpi, figsize=(8,6))

		self.obs_temp_plot = self.fig.add_subplot(111)
		
		self.exp_temp_plot = self.fig.add_subplot(111)
		self.exp_temp_plot.set_xlabel('Time (s)')
		self.exp_temp_plot.set_ylabel('Temp (deg C)')

		self.canvas = FigureCanvasTkAgg(self.fig, master=self)
		self.canvas.show()
		# self.canvas.get_tk_widget().pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=1)

		self.canvas._tkcanvas.grid(column=3, row=1, columnspan=5, rowspan=19)
		# self.canvas.grid(column=3, row=1, rowspan=4)

		# Column 4
		self.Stop_button = Tkinter.Button(self, text="Stop", background="red", foreground="black", command=self.stop_button_handler)
		self.Stop_button.grid(column=4,row=0)

		# Column 5
		self.Stop_button = Tkinter.Button(self, text="Hold Preheat", command=self.hold_preheat_handler)
		self.Stop_button.grid(column=5,row=0)

		# Column 6
		self.Stop_button = Tkinter.Button(self, text="Hold Soak", command=self.hold_soak_handler)
		self.Stop_button.grid(column=6,row=0)

		# Column 7
		self.Stop_button = Tkinter.Button(self, text="Hold Reflow", command=self.hold_reflow_handler)
		self.Stop_button.grid(column=7,row=0)

	def sampling(self):
		if(self.ser != None):
			if(not self.ser.inbox.empty()):
				buf = self.ser.inbox.get()
				buf_tuple = buf.split()
				# print "buf: %s" % buf_tuple
				# print "buf[0]: %s" % buf_tuple[0]
				# print "buf[1]: %s" % buf_tuple[1]
				# print "buf[2]: %s" % buf_tuple[2]

				if(buf_tuple[0] == "data"):
					# print "observed temp: %s" % buf_tuple[2]
					self.obs_temp_data.append(buf_tuple[2])

					# print "expected temp: %s" % buf_tuple[1]
					self.exp_temp_data.append(buf_tuple[1])

					self.obs_temp_plot.clear()
					self.exp_temp_plot.clear()

					self.obs_temp_plot.plot(range(len(self.obs_temp_data)), self.obs_temp_data, 'k-')#, label="Observed Temp")
					self.exp_temp_plot.plot(range(len(self.exp_temp_data)), self.exp_temp_data, 'r-')#, label="Expected Temp")
			
				elif(buf_tuple[0] == "param"):
					# print "Parameters"
					self.preheat_P.set(float(buf_tuple[1]))
					self.preheat_I.set(float(buf_tuple[2]))
					self.preheat_D.set(float(buf_tuple[3]))
					self.soak_P.set(float(buf_tuple[4]))
					self.soak_I.set(float(buf_tuple[5]))
					self.soak_D.set(float(buf_tuple[6]))
					self.reflow_P.set(float(buf_tuple[7]))
					self.reflow_I.set(float(buf_tuple[8]))
					self.reflow_D.set(float(buf_tuple[9]))
					self.cool_P.set(float(buf_tuple[10]))
					self.cool_I.set(float(buf_tuple[11]))
					self.cool_D.set(float(buf_tuple[12]))
					self.preheat_temp.set(float(buf_tuple[13]))
					self.soak_min.set(float(buf_tuple[14]))
					self.soak_max.set(float(buf_tuple[15]))
					self.soak_time.set(float(buf_tuple[16]))
					self.reflow_max.set(float(buf_tuple[17]))

				self.canvas.show()
	
		self.after(10, self.sampling)
	


if __name__ == "__main__":
	# try:
	gui = reflow_GUI(None)
	gui.title("Reflow Oven of DOOM!!!")

	gui.sampling()
	
	gui.mainloop()
	gui.stop_prog()

	# except KeyboardInterrupt:
	# 	print "Keyboard interrupt!!!"
	# 	gui.stop_prog()

