"""
@author: mkturkcan
@translator: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""


class Location:
    """
    A class to represent a location in the simulated environment.
    一个代表模拟环境的位置的类

    Attributes:
    ----------
    name : str
        The name of the location.
    description : str
        A brief description of the location.

    Methods:
    -------
    describe():
        Prints the description of the location.
    """

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __str__(self):
        return self.name

    def describe(self):
        print(self.description)


class Locations:
    """
    A class to represent a collection of locations in the simulated environment.
    一个代表模拟环境的位置集合的类

    Attributes:
    ----------
    locations : dict
        A dictionary of locations, with keys as the location names and values as Location objects.

    Methods:
    -------
    add_location(name, description):
        Adds a new location to the collection.
    
    get_location(name):
        Returns the Location object with the given name.
    
    __str__():
        Returns a string representation of the collection of locations.
    """

    def __init__(self):
        self.locations = {}

    def add_location(self, name, description):
        self.locations[name] = Location(name, description)

    def get_location(self, name):
        return self.locations.get(name)
    def __str__(self):
        return "\n".join([str(location) for location in self.locations.values()])