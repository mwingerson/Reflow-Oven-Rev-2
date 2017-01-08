/* reflow oven */

#include <PID_v1.h>
#include <SPI.h>
#include <TC1.h>

// FSM definitions
#define REST_ST 			0
#define PREHEAT_ST 			1
#define WARM_ST 			2
#define SOAK_ST 			3
#define REFLOW_ST 			4
#define COOL_ST 			5
#define HOLD_PREHEAT_ST		6
#define HOLD_SOAK_ST		7
#define HOLD_REFLOW_ST		8

const char* state_names[] = {"Rest State", "Preheat State", "Warm State", "Soak State", "Reflow State", "Cool State", "Hold Preheat State", "Hold Soak State", "Hold Reflow State"};

int state = REST_ST;

float oven_temp = 0.0;

// PID values
float preheat_P = 13.0;
float preheat_I = 0.025;
float preheat_D = 250;
float soak_P = 45.0;
float soak_I = 0.1;
float soak_D = 800.0;
float reflow_P = 45.0;
float reflow_I = 0.1;
float reflow_D = 800.0;
float cool_P = 13.0;
float cool_I = 0.025;
float cool_D = 250.0;

// reflow parameters
float preheat_temp = 50.0;
float soak_min = 140.0;
float soak_max = 160.0;
float soak_time = 75000.0;
float reflow_max = 215.0;

#define buf_size 512
char* temp_ptr = NULL;
char outbox[buf_size];
char inbox[buf_size];

int last_data;
int last_reflow;
int last_timer;

// slow PWM variables
#define SPWM_window 500
unsigned int last_SPWM = 0;
unsigned SPWM_comp = 0;

#define relay_pin 25
#define chipSelectPin SS

// PID declarations
double PID_input;
double setpoint;
double PID_output;
double Kp;
double Ki;
double Kd;

// PID myPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, DIRECT);
PID myPID(&PID_input, &PID_output, &setpoint, Kp, Ki, Kd, DIRECT);

TC1 myTMP;

void send_data(){
	int i;
	if(millis()-last_data > 1000){

		for(i=0; i<buf_size; i++)
			outbox[i] = 0;
	
		// sprintf(outbox, "data %4.2f %4.2f", exp_sc*sin(exp_temp), obs_sc*sin(obs_temp));
		sprintf(outbox, "data %4.2f %4.2f %s", oven_temp, setpoint, state_names[state]);
		
		Serial.println(outbox);
		// Serial.print("SPWM_comp: ");
		// Serial.println(SPWM_comp);

		last_data = millis();
	}
}

void read_serial(){
	int i;
	// char *ptr;
	if(Serial.available() > 0){
		// Serial.readline('\r', inbox, buf_size);
		// Serial.readBytesUntil('\r', inbox, buf_size);
		Serial.readBytesUntil('\r', inbox, buf_size);

		inbox[strlen(inbox)] = 0;

		// Serial.print("Read from serial: ");
		// Serial.println(inbox);

		temp_ptr = strtok(inbox, " ");

		if(temp_ptr != NULL){	
			if(!strcmp(temp_ptr, "start")){
				Serial.println("Starting reflow");
				state = PREHEAT_ST;
				setpoint = preheat_temp;
				myPID.SetTunings(preheat_P, preheat_I, preheat_D);
			}

			else if(!strcmp(temp_ptr, "stop")){
				Serial.println("Stopping reflow");
				state = REST_ST;
			}

			else if(!strcmp(temp_ptr, "get_param")){
				Serial.println("Getting params");
				send_params();
			}

			else if(!strcmp(temp_ptr, "update")){				
				temp_ptr = strtok(NULL, " ");
				preheat_P = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				preheat_I = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				preheat_D = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				soak_P = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				soak_I = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				soak_D = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				reflow_P = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				reflow_I = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				reflow_D = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				cool_P = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				cool_I = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				cool_D = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				preheat_temp = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				soak_min = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				soak_max = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				soak_time = atof(temp_ptr);

				temp_ptr = strtok(NULL, " ");
				reflow_max = atof(temp_ptr);

				for(i=0; i<buf_size; i++)
					outbox[i] = 0;

				send_params();
			}

			else if(!strcmp(temp_ptr, "hold_preheat")){
				Serial.println("Holding preheat");
				state = HOLD_PREHEAT_ST;
			}

			else if(!strcmp(temp_ptr, "hold_soak")){
				Serial.println("Holding Soak");
				state = HOLD_SOAK_ST;
			}

			else if(!strcmp(temp_ptr, "hold_reflow")){
				Serial.println("Holding Reflow");
				state = HOLD_REFLOW_ST;
			}

			else{
				Serial.println("Unrecognized command");
			}
		}
		for(i=0; i<buf_size; i++)
			inbox[i] = 0;
	}
}

void send_params(){
	sprintf(outbox, "param %4.6f %4.6f %4.6f %4.6f %4.6f %4.6f %4.6f %4.6f %4.6f %4.6f %4.6f %4.6f %4.6f %4.6f %4.6f %4.6f %4.6f", \
	preheat_P, preheat_I, preheat_D, 	\
	soak_P, soak_I, soak_D, 			\
	reflow_P, reflow_I, reflow_D, 		\
	cool_P, cool_I, cool_D, 			\
	preheat_temp, soak_min, soak_max, soak_time, reflow_max);

	Serial.println(outbox);
}

void slow_PWM(){
	if(SPWM_comp == 0){
		digitalWrite(relay_pin, LOW);
		// Serial.println("Off");
	}
	else if(millis() < last_SPWM + SPWM_window)
		if(millis() < last_SPWM + SPWM_comp){
			digitalWrite(relay_pin, HIGH);
			// Serial.println("On");
		}
		else{
			digitalWrite(relay_pin, LOW);
			// Serial.println("Off");
		}
	else{
		digitalWrite(relay_pin, LOW);
		// Serial.println("Off");
		last_SPWM = millis();
	}
	// Serial.print("Slow PWM: ");
	// Serial.println(SPWM_comp);
}

void setup() {
	//init serial 
	Serial.begin(115200);

	//startup TC1
	SPI.begin();
	myTMP.begin(chipSelectPin);
	pinMode(chipSelectPin, OUTPUT); 

	//initialize sensor  
	digitalWrite(chipSelectPin, HIGH); 

	pinMode(relay_pin, OUTPUT); 
	digitalWrite(relay_pin, LOW);  
	delay(100);

	//setup PID
	oven_temp = myTMP.getTemp();
	setpoint = preheat_temp;

	myPID.SetMode(AUTOMATIC);
	myPID.SetSampleTime(5000);
	myPID.SetOutputLimits(0, (int)SPWM_window);

	last_data = millis();
	last_SPWM = last_data;
	last_reflow = last_data;
	last_timer = last_data;
}

void loop() {
	//handle the send data heartbeat
	if(state != REST_ST){
		myPID.Compute();
		SPWM_comp = PID_output;
	}

	//hand incoming serial data 
	read_serial();
	send_data();
	slow_PWM();

	if(millis()-last_reflow > 1000){

		oven_temp = myTMP.getTemp();
		PID_input = (float)oven_temp;

		switch(state){
			case REST_ST:
				// Serial.println("Rest State");
				SPWM_comp = 0;
				last_timer = millis();
				break;

			//Preheat Zone
			//Hold at the starting temp to equilibrate the oven
			case PREHEAT_ST:
				// Serial.println("Preheat State");
				// Serial.print("timer check: ");
				// Serial.println(millis() - last_timer);

				if(oven_temp > preheat_temp+2 || oven_temp < preheat_temp-2)
					last_timer = millis();

				if(millis() - last_timer > 20000){
					state = WARM_ST;
					myPID.SetTunings(soak_P, soak_I, soak_D);
					setpoint = soak_min;
				}
				break;

			case WARM_ST:
				// Serial.println("Warm State");

				if(oven_temp > soak_min){
					state = SOAK_ST;
					setpoint = soak_max;
					last_timer = millis();
				}

				break;

			case SOAK_ST:
				// Serial.println("Soak State");
				if(millis() - last_timer > soak_time){
					state = REFLOW_ST;
					setpoint = reflow_max;
					myPID.SetTunings(reflow_P, reflow_I, reflow_D);					
				}

				break;

			case REFLOW_ST:
				// Serial.println("Reflow State");
				if(oven_temp > reflow_max){
					state = COOL_ST;
					setpoint = preheat_temp;
					myPID.SetTunings(preheat_P, preheat_I, preheat_D);
				}

				break;

			case COOL_ST:
				// Serial.println("Cool State");
				if(oven_temp < preheat_temp){
					state = REST_ST;
					setpoint = 0;
				}
				break;

			case HOLD_PREHEAT_ST:
				Serial.println("Holding Preheat State");
				myPID.SetTunings(preheat_P, preheat_I, preheat_D);
				setpoint = preheat_temp;
				break;

			case HOLD_SOAK_ST:
				Serial.println("Holding Soak State");
				setpoint = (soak_min+soak_max)/2;
				myPID.SetTunings(soak_P, soak_I, soak_D);
				break;

			case HOLD_REFLOW_ST:
				Serial.println("Holding Reflow State");
				setpoint = reflow_max;
				myPID.SetTunings(reflow_P, reflow_I, reflow_D);
				break;

			default:
				SPWM_comp = 0;
				state = REST_ST;
				Serial.println("ERROR!!!!!!");
				break;

		}

		last_reflow = millis();		
	}
}
