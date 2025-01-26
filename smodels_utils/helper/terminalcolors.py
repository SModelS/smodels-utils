#!/usr/bin/env python3

"""
.. module:: terminalcolors
    :synopsis: super simple module for terminal colors

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

GREEN, YELLOW, RED, RESET, CYAN, MAGENTA, BLUE = [ "" ] * 7

try:
    from colorama import Fore as __c
    GREEN, YELLOW, RED, RESET = __c.GREEN, __c.YELLOW,  __c.RED, __c.RESET
    CYAN, MAGENTA, BLUE = __c.CYAN, __c.MAGENTA, __c.BLUE
except Exception as e:
    print ( f"[terminalcolors] no colors: {e}" )
    pass
