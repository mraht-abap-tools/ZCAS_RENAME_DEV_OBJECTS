*---------------------------------------------------------------------*
*    program for:   TABLEFRAME_#CAS#EWM_T_CNF_VAR
*---------------------------------------------------------------------*
FUNCTION TABLEFRAME_#CAS#EWM_T_CNF_VAR     .

  PERFORM TABLEFRAME TABLES X_HEADER X_NAMTAB DBA_SELLIST DPL_SELLIST
                            EXCL_CUA_FUNCT
                     USING  CORR_NUMBER VIEW_ACTION VIEW_NAME.

ENDFUNCTION.
