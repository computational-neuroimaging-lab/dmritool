#!/bin/bash - 

matlab -nosplash -nodesktop  -r " \
publish('demo_separate_sets.m');\
publish('demo_separate_t4_1shell.m');\
publish('demo_separate_t4_28x3.m');\
publish('demo_separate_HCPQ390x3_30x3.m');\
publish('demo_separate_HCPQ390x3_45x3.m');\
publish('demo_mutishell_IMOC_1Opt_CNLO.m');\
publish('demo_singleshell_IMOC_1Opt_CNLO.m');\
exit;"



