P3Auth
======

Simple Authentication module used by PricesPaidGUI and PricesPaidAPI.  This project has almost no stand-alone value apart from the P3 project.  

It is, however, a derived [CAS](https://wiki.jasig.org/display/CAS/Home) (Central Authentication Service) client.  As such, it might be interesting to anyone who wants a Python CAS client.
It is basecd on the file [pycas.py](https://wiki.jasig.org/display/CASC/Pycas) by Jon Rifkin that may be valuable to someone doing CAS authentication that is NOT using CGI as the original file did.

This is part of the PricesPaid (P3) Project
--------------------------------------

The PricesPaid (P3) project is market research tool to allow search of purchase transactions.  It is modularized into 4 github repositories:

1. [PricesPaidGUI](https://github.com/XGov/PricesPaidGUI), 
2. [PricesPaidAPI](https://github.com/presidential-innovation-fellows), 
3. [MorrisDataDecorator](https://github.com/presidential-innovation-fellows/MorrisDataDecorator), 
4. [P3Auth](https://github.com/XGov/P3Auth).  

To learn how to install the system, please refer to the documentation in the PricesPaidGUI project.

The name "PricesPaid" is descriptive: this project shows you prices that have been paid for things.  However, the name is applied to many projects, so "P3" is the specific name of this project.

# Licensing: derived work of Pycas.py

The pycas.py is copyright Jon Rifkin 2011.  I have made a modified version (a derived work) that is not based on CGI but more appropriately callable by WSGI.  This file is released under the Apache 2.0 license.



