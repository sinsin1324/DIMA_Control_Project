#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>
#include <unistd.h>
#include <chrono>
#include <thread>
#include "command_packet.h"
#include "JetsonGPIO.h"

#define NUM_THREADS 5
#define Q_SIZE 30

using namespace GPIO;

int header = 0;
struct packet *command_qp, *current_command, command, command_queue[Q_SIZE];
int packet_pos = -1;

//executes the next command in the queue
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

static void actuator_command(){}
static void kill(){}
static void revive(){}
static void logging(){}
static void heartbeat(){}
static void control_loop(){}

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
    initialise pointer to command queue
    command_qp = &command_queue[0];
    current_command = &command;

    (command_qp)->c_header.cls = 0x0000;
    (command_qp)->c_header.length = 1;

    create threads for processes
    pthread_t tid[NUM_THREADS];
    pthread_create(&tid[0], NULL, control, NULL);
    pthread_join(tid[0], NULL);
    load_command();
    exit(0);
}
