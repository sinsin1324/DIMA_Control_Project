#include <stdio.h>
#include <sys/file.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include<ctype.h>
#include <unistd.h>
#include <chrono>
#include <thread>
#include <mutex>
#include <fcntl.h> // Contains file controls like O_RDWR
#include <errno.h> // Error integer and strerror() function
#include <termios.h> // Contains POSIX terminal control definitions
#include <unistd.h> // write(), read(), close()
#include <string>
#include <algorithm>
#include <iostream>

#include "command_packet.h"
#include "JetsonGPIO.h"
#include "jetson.h"

using namespace GPIO;

header in_h = 0;
packet_pos, in_pp = -1;

static void void initPort(int *xbee_port) {
    struct termios tty;

    //change configuration settings for serial ports
    tcgetattr(*xbee_port, &tty);

    //set parity bit
    tty.c_cflag &= ~PARENB;

    //clear stop bit - one stop bit used
    tty.c_cflag &= ~CSTOPB;

    //set number of bits per byte
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8; // 8 bits per byte

    //disable hardware flow control
    tty.c_cflag &= ~CRTSCTS;

    //disable xon/xoff
    tty.c_iflag &= ~(IXON | IXOFF | IXANY);

    //turn on read, ignore control lines
    tty.c_cflag |= CREAD | CLOCAL;

    //disable canonical mode
    tty.c_lflag &= ~ICANON;

    //disable extra bits which are rendered useless by canonical mode
    tty.c_lflag &= ~ECHO; // Disable echo
    tty.c_lflag &= ~ECHOE; // Disable erasure
    tty.c_lflag &= ~ECHONL; // Disable new-line echo

    //disable signal chars
    tty.c_lflag &= ~ISIG;

    //disable special byte handling
    tty.c_iflag &= ~(IGNBRK|BRKINT|PARMRK|ISTRIP|INLCR|IGNCR|ICRNL);
    
    //disable output handling of of bytes
    tty.c_oflag &= ~OPOST;
    tty.c_oflag &= ~ONLCR;

    //setting minimum characters to be read and timeout
    tty.c_cc[VMIN] = 6;
    tty.c_cc[VTIME] = 10; //tenths of a second

    // Set in/out baud rate to be 230400
    cfsetispeed(&tty, B230400);
    cfsetospeed(&tty, B230400);
    
    // Save tty settings, also checking for error
    tcsetattr(*xbee_port, TCSANOW, &tty);
}

static void *telemetry(void *vargp) {

        // int xbee_port = open("/dev/tty.usbserial-DN02SSJ0", O_RDWR | O_NOCTTY | O_NDELAY);
        int xbee_port = open("/dev/ttyUSB0", O_RDWR | O_NOCTTY | O_NDELAY);

        if (xbee_port < 0) {
            printf("Error %i from open: %s\n", errno, strerror(errno));
        }

        initPort(&xbee_port);

        while (1) {
            FILE *fp;
            int c;
            // fp = fopen("/dev/tty.usbserial-DN02SSJ0", "r+");
            fp = fopen("/dev/ttyUSB0", "r+");
            if (fp) {
                while ((c = getc(fp)) != EOF){
                    if (isdigit(c)) {
                        if (!in_h) {
                            q_lock.lock();
                            (command_qp+packet_pos)->c_header.cls = c - '0';
                            c = getc(fp)
                            (command_qp+packet_pos)->c_header.length = c - '0';
                            in_h = 1;
                            q_lock.unlock();
                            std::cout << "CLASS: " << (command_qp+packet_pos)->c_header.cls << std::endl
                                << "SIZE: " << (command_qp+packet_pos)->c_header.length << std::endl;
                        } else {
                            q_lock.lock();
                            if ((command_qp+packet_pos)->c_header.cls == 0x0000) {
                                char temp_sys[3] = {'a','a','a'};
                                try {
                                    temp_sys[0] = c;
                                    c = getc(fp);
                                    temp_sys[1] = c;
                                    c = getc(fp);
                                    temp_sys[2] = c;
                                } catch(...) {
                                    pass;
                                }
                                system_mode_command total_sys = 0;
                                int counter_sys = 0;
                                for (int i = 2; i > -1; i--) {
                                    if (isdigit(temp_sys[i])) {
                                        total_sys += (temp_sys[i]-'0') * pow(10, counter_sys);
                                        counter_sys++;
                                    }
                                }
                                (command_qp+packet_pos)->c_data.c_system_mode = total_sys;
                            } else if ((command_qp+packet_pos)->c_header.cls == 0x0001) {
                                char temp_flo[6] = {'a','a','a','a','a','a'};
                                int temp_ls[4] = {1,2,3,5};
                                for (int i = 0; i < 4; i++) {
                                    float curr_act = 0;
                                    for (int j = 0; j < 6; j++) {
                                        temp_flo[j] = c;
                                        if (j!=5) getc(fp);
                                    }

                                    int power = 2;
                                    for (int k = 0; k < 4; k++) {
                                        curr_act += (temp_flo[temp_ls[k]]-'0') * pow(10, power);
                                        power--;
                                    }
                                    if (i==0) {
                                        (command_qp+packet_pos)->c_data.c_actuator.throttle == curr_act;
                                    } else if (i==1) {
                                        (command_qp+packet_pos)->c_data.c_actuator.steering == curr_act;
                                    } else if (i==2) {
                                        (command_qp+packet_pos)->c_data.c_actuator.tail_velocity == curr_act;
                                    } else if (i==3) {
                                        (command_qp+packet_pos)->c_data.c_actuator.aux2 == curr_act;
                                    }
                                }
                            }
                            q_lock.unlock();
                            in_h = 0;
                        }
                    sleep(0.05);
                }
                fclose(fp);
            }
        }
}

//loads the next command in the queue
static void load_command() {
    packet_pos = (packet_pos+1)%30;
    if (!header) {
        header = !header;
        current_command->c_header.crc = (command_qp+packet_pos)->c_header.crc;
        current_command->c_header.cls = (command_qp+packet_pos)->c_header.cls;
        current_command->c_header.length = (command_qp+packet_pos)->c_header.length;
    }
    if (header) {
        if (current_command->c_header.cls == 0x0000){
            current_command->c_data.c_system_mode = (command_qp+packet_pos)->c_data.c_system_mode;
        } else if (current_command->c_header.cls == 0x0001) {
            current_command->c_data.c_actuator.throttle = (command_qp+packet_pos)->c_data.c_actuator.throttle;
            current_command->c_data.c_actuator.steering = (command_qp+packet_pos)->c_data.c_actuator.steering;
            current_command->c_data.c_actuator.tail_velocity = (command_qp+packet_pos)->c_data.c_actuator.tail_velocity;
            current_command->c_data.c_actuator.aux2 = (command_qp+packet_pos)->c_data.c_actuator.aux2;
        } else if (current_command->c_header.cls == 0x0007) {
            current_command->c_data.c_loop_commands.speed = (command_qp+packet_pos)->c_data.c_loop_commands.speed;
            current_command->c_data.c_loop_commands.heading = (command_qp+packet_pos)->c_data.c_loop_commands.heading;
            current_command->c_data.c_loop_commands.position = (command_qp+packet_pos)->c_data.c_loop_commands.position;
            current_command->c_data.c_loop_commands.damper = (command_qp+packet_pos)->c_data.c_loop_commands.damper;
        }
    }
    header =! header;
    printf("Command Loaded\n");
}

// executes the current loaded command
static void execute_command() {
    if (current_command->c_header.cls == 0x0000) {
	system_mode();
    }  else if (current_command->c_header.cls == 0x0001) {
	actuator_command();
    } else if (current_command->c_header.cls == 0x0002) {
	kill();
    } else if (current_command->c_header.cls == 0x0003) {
	revive();
    } else if (current_command->c_header.cls == 0x0004) {
	logging();
    } else if (current_command->c_header.cls == 0x0005) {
	logging();
    } else if (current_command->c_header.cls == 0x0006) {
	heartbeat();
    } else if (current_command->c_header.cls == 0x0007) {
	control_loop();
    } 
}

static void system_mode(){
	int a2 = current_command->c_data.c_system_mode >> 6; 
	int a1 = current_command->0b11&(c_data.c_system_mode >> 4);
	int steer = current_command->0b11&(c_data.c_system_mode >> 2);
	int thrott = current_command->0b11&c_data.c_system_mode;

    	 
}

static void actuator_command(){pass;}
static void kill(){pass;}
static void revive(){pass;}
static void logging(){pass;}
static void heartbeat(){pass;}
static void control_loop(){pass;}

//function for control thread
static void *control(void *vargp){
    struct command_header *header, header_data;
    header = &header_data;
    header->cls = 0x0001;
    header->length = 1;
    printf("HI\n");
    printf("Class: %d\n", header->cls);
    printf("Length: %d\n", header->length);
    return NULL;
}

int main(void) {
    setmode(BCM);
    // initialise pointer to command queue
    command_qp = &command_queue[0];
    current_command = &command;

    (command_qp)->c_header.cls = 0x0000;
    (command_qp)->c_header.length = 1;

    // create threads for processes
    pthread_t tid[NUM_THREADS];
    pthread_create(&tid[0], NULL, telemetry, NULL);
    pthread_join(tid[0], NULL);
    pthread_create(&tid[1], NULL, control, NULL);
    pthread_join(tid[1], NULL);
    load_command();
    exit(0);
}
