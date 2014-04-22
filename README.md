P3Auth
======

Simple Authentication module used by PricesPaidGUI and PricesPaidAPI.  This project has almost no stand-alone value apart from the P3 project.  

It is, however, a derived [CAS](https://wiki.jasig.org/display/CAS/Home) (Central Authentication Service) client.  As such, it might be interesting to anyone who wants a Python CAS client.
It is basecd on the file [pycas.py](https://wiki.jasig.org/display/CASC/Pycas) by Jon Rifkin that may be valuable to someone doing CAS authentication that is NOT using CGI as the original file did.

This is part of the PriceHistory (P3) Project
--------------------------------------

The PriceHistory (P3) project is market research tool to allow search of purchase transactions.  It is modularized into 5 github repositories:

1. [PriceHistoryInstall](https://github.com/18F/PriceHistoryGUI),
2. [PriceHistoryGUI](https://github.com/18F/PriceHistoryGUI), 
3. [PriceHistoryAPI](https://github.com/18F/PriceHistoryAPI), 
4. [MorrisDataDecorator](https://github.com/18F/MorrisDataDecorator), 
5. [PriceHistoryAuth](https://github.com/18F/PriceHistoryAuth).  

To learn how to install the system, please refer PriceHistoryInstall project, which contains a Vagrant install script.  That repo is actively under development in preparation of the Houston Hackathon.

The name "PriceHistory" is descriptive: this project shows you prices that have been paid for things.  However, the name is applied to many projects, so "P3" is the specific name of this project.

# Licensing: derived work of Pycas.py

The pycas.py is copyright Jon Rifkin 2011.  I have made a modified version (a derived work) that is not based on CGI but more appropriately callable by WSGI.  This file is released under the Apache 2.0 license.



