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
    # print ( f"[terminalcolors] no colors: {e}" )
    GREEN, YELLOW, RED, RESET = "\033[32m", "\033[33m", "\033[91m", "\033[0m"
    CYAN, MAGENTA, BLUE = "\033[36m", "\033[35m", "\033[34m"
