*---------------------------------------------------------------------*
*    view related data declarations
*---------------------------------------------------------------------*
*...processing: #CAS#EWM_T_CNF_VAR..................................*
DATA:  BEGIN OF STATUS_#CAS#EWM_T_CNF_VAR                .   "state vector
         INCLUDE STRUCTURE VIMSTATUS.
DATA:  END OF STATUS_#CAS#EWM_T_CNF_VAR                .
CONTROLS: TCTRL_#CAS#EWM_T_CNF_VAR
            TYPE TABLEVIEW USING SCREEN '0001'.
*.........table declarations:.................................*
TABLES: *#CAS#EWM_T_CNF_VAR                .
TABLES: #CAS#EWM_T_CNF_VAR                 .

* general table data declarations..............
  INCLUDE LSVIMTDT                                .
