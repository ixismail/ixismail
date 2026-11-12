"""Generates the GitHub profile README's images. Run with `python -m profilegen` (see __main__).

Animations use the "values" trick: attributes hold the finished frame and SMIL rewinds it at load,
so renderers without SMIL still show the finished image.
"""
