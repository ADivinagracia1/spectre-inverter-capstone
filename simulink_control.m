clc;
clear;
close all;
open_system('example')

sim_time_step = 0.01;

% start the simulation and pause the simulation, waiting for singal from python
set_param(gcs,'SimulationCommand','start','SimulationCommand','pause');

% open a server, it will block until a client connect to it
s = tcpip('127.0.0.1', 54320,  'NetworkRole', 'server');
fopen(s);
fprintf("Socket opened");

count=0;
% main loop
while  count<1000 % can be changed      
    while(1) %loop, until read some data
        nBytes = get(s,'BytesAvailable');
        if nBytes>0
            break;
        end
    end
    command = fread(s,nBytes);
    try
        pwmdata = jsondecode(char(command()'));

        if isempty(pwmdata)
            data=0;
        end

        % set a paramter in the simulink model using the data get from python
        set_param('example/K','Gain',num2str(pwmdata.A));
        set_param('example/K1','Gain', num2str(pwmdata.B))
        set_param('example/K2','Gain',num2str(pwmdata.C));

        % run the simulink model for a step
        set_param(gcs, 'SimulationCommand', 'step');  

        % pause the simulink model and send some data to python
        %pause(0.1);
        %u=states.data(end,:)
        %fwrite(s, jsonencode(u));
        count=count+1;
    catch exception
        fprintf(exception);
    end
end
fclose(s);

