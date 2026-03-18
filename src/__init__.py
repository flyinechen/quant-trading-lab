"""
Quantitative Trading Lab
量化交易研究实验室

A comprehensive quantitative trading research and execution platform.
"""

__version__ = "0.1.0"
__author__ = "flyinechen"
__email__ = "flyinechen@github.com"

from .utils.config import Config
from .utils.logger import get_logger

__all__ = ["Config", "get_logger"]
