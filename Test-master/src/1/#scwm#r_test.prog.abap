*&---------------------------------------------------------------------*
*& Report ziot_r_test
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT ziot_r_test.

DATA:
  BEGIN OF ls_data,
    modtext TYPE modtext_d,
  END OF ls_data,
  lt_data LIKE TABLE OF ls_data.

CLASS cl_event_handler DEFINITION.

  PUBLIC SECTION.

    CLASS-DATA:
      lo_popup TYPE REF TO cl_salv_table.

    CLASS-METHODS on_function_click
      FOR EVENT if_salv_events_functions~added_function
        OF cl_salv_events_table IMPORTING e_salv_function.
ENDCLASS.

CLASS cl_event_handler IMPLEMENTATION.

  METHOD on_function_click.

    CASE e_salv_function.
      WHEN 'GOON'.
        lo_popup->close_screen( ).
*       do action
      WHEN 'ABR'.
        lo_popup->close_screen( ).
*       cancel
    ENDCASE.
  ENDMETHOD.
ENDCLASS.

* Eventhandler für neuen Button
CLASS lcl_events DEFINITION.
  PUBLIC SECTION.
* Bezeichner des Buttons
    CONSTANTS: co_btn_xl_export TYPE string VALUE 'BTN_XL_EXPORT'.

    CLASS-METHODS : on_toolbar_click FOR EVENT added_function OF cl_salv_events_table
      IMPORTING
          e_salv_function
          sender.
ENDCLASS.

CLASS lcl_events IMPLEMENTATION.
  METHOD on_toolbar_click.
    CASE e_salv_function.
      WHEN co_btn_xl_export.
        MESSAGE co_btn_xl_export TYPE 'S'.
    ENDCASE.
  ENDMETHOD.
ENDCLASS.

START-OF-SELECTION.
  PERFORM main.

FORM main.

  DATA:
    lo_popup  TYPE REF TO cl_salv_table,
    lo_events TYPE REF TO cl_salv_events_table.

  SELECT *
    INTO CORRESPONDING FIELDS OF TABLE lt_data
    FROM modsapt
    WHERE sprsl = 'EN'
      AND name LIKE 'S%'.

  TRY.
      CALL METHOD cl_salv_table=>factory
        IMPORTING
          r_salv_table = lo_popup
        CHANGING
          t_table      = lt_data.

      lo_popup->get_functions( )->set_all( abap_false ).
      lo_popup->get_functions( )->add_function( name = |{ lcl_events=>co_btn_xl_export }|
                                                icon = |{ icon_export }|
                                                text = 'Export'
                                                tooltip = 'Daten exportieren'
                                                position = if_salv_c_function_position=>right_of_salv_functions ).

**     register handler for actions
*      lo_events = lo_popup->get_event( ).
*      SET HANDLER cl_event_handler=>on_function_click FOR lo_events.
*     save reference to access object from handler
*      cl_event_handler=>lo_popup = lo_popup.

*     use gui-status ST850 from program SAPLKKB
*      lo_popup->set_screen_status( pfstatus      = 'ST850'
*                                   report        = 'SAPLKKBL' ).

*     display as popup
      lo_popup->set_screen_popup( start_column = 1
                                  end_column   = 60
                                  start_line   = 1
                                  end_line     = 10 ).

      lo_popup->display( ).

    CATCH cx_root INTO DATA(lx_root).
      WRITE: / lx_root->get_longtext( ).
  ENDTRY.
ENDFORM.
