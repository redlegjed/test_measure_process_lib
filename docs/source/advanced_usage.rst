TMPL Advanced usage
===================

Sequence states
----------------

When a *TestManager* sequence is executed using the *run()* method it creates a loop. Before starting the loop a table of setup conditions is created. Each row of the table represents a combination of setup conditions. Each iteration of the loop is one row of the table. Within this loop there are particular states where *Measurement* classes can be executed. These states are *Startup*, *Setup*, *Main*, *After*, *Teardown* and *Error*. The sequence loop runs in the order below, with the states shown in **bold**.

* Build setup conditions table
* **Startup** : Run anything that needs setting up
* Load first set of conditions from table
    - **Setup** stage
    - For each condition in the set
        + Set condition to current value
        + Run any measurements for this condition
    - **Main** : Run main measurements
    - **After** : Run teardown for current set of conditions
* **Teardown**: Run global teardown measurements, e.g. shutdown, store results
* **Error** : Run when error occurs.

*Measurement* classes can be set to execute in one or more of these states using methods with the prefix *run_*.

* *run_on_startup* : Run before any conditions have been set at the **Startup** state
* *run_on_setup* : Run after a specific condition has been set in the **Setup** state
* *run_on_main* : Run in the main loop. This is the default state and does not need to be explicitly set.
* *run_after*: Run after all main measurements have been executed for one set of conditions.
* *run_on_teardown*: Run at the end of the sequence. This is useful for shutting down.
* *run_on_error*: Run when an error occurs






Sequencing
----------
TODO


Processing
----------
TODO


Customisation
-------------
TODO