#include <mutex>

#define NUM_THREADS 5
#define Q_SIZE 30
#define pass (void)0

int header, in_h;
char cls1;
struct packet *command_qp, *current_command, command, command_queue[Q_SIZE];
int packet_pos, in_pp;
std::mutex q_lock, curr_lock;
