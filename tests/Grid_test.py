import unittest

from Grid import Grid


class GridStrategy_Test(unittest.TestCase):
    
    def setUp(self) -> None:
        return super().setUp()
    
    def test_init(self):
        # throw ValueError if upper_price < lower_price
        self.assertRaises(ValueError, Grid, 1000,2000,100)

        # generates [2000, 1800, 1600, 1400, 1200, 1000]
        grid = Grid(2000, 1000, 200)
        self.assertEquals(len(grid.grid_lines), 6)
        self.assertEquals(grid.grid_lines[0], 2000)
        self.assertEquals(grid.grid_lines[5], 1000)

        # generates [2000, 1700, 1400, 1100]
        grid = Grid(2000, 1000, 300)
        self.assertEquals(len(grid.grid_lines), 4)
        self.assertEquals(grid.grid_lines[0], 2000)
        self.assertEquals(grid.grid_lines[3], 1100)
    
    def test_num_gridlines_below(self):
        
        # generates [2000, 1800, 1600, 1400, 1200, 1000]
        grid = Grid(2000, 1000, 200)
        self.assertEquals(grid.num_gridlines_below(3000), 6)
        self.assertEquals(grid.num_gridlines_below(2000), 6)

        self.assertEquals(grid.num_gridlines_below(1900), 5)
        self.assertEquals(grid.num_gridlines_below(1800), 5)
        self.assertEquals(grid.num_gridlines_below(1100), 1)

        self.assertEquals(grid.num_gridlines_below(1000), 0)
        self.assertEquals(grid.num_gridlines_below(100), 0)
    
    def test_num_gridlines_below(self):
        
        # generates [2000, 1800, 1600, 1400, 1200, 1000]
        grid = Grid(2000, 1000, 200)
        self.assertEquals(grid.num_gridlines_above(3000), 0)
        self.assertEquals(grid.num_gridlines_above(2000), 0)

        self.assertEquals(grid.num_gridlines_above(1900), 1)
        self.assertEquals(grid.num_gridlines_above(1800), 2)
        self.assertEquals(grid.num_gridlines_above(1100), 5)

        self.assertEquals(grid.num_gridlines_above(1000), 6)
        self.assertEquals(grid.num_gridlines_above(100), 6)
    
    def test_price_below(self):
        grid = Grid(2000, 1000, 200)
        self.assertEquals(grid.price_below(3000), 2000)
        self.assertEquals(grid.price_below(2000), 2000)
        self.assertEquals(grid.price_below(1999), 1800)
        self.assertEquals(grid.price_below(1000), 1000)
        
        self.assertRaises(ValueError, grid.price_below, 100)

    def test_price_above(self):
        grid = Grid(2000, 1000, 200)
        self.assertEquals(grid.price_above(2000), 2000)
        self.assertEquals(grid.price_above(1999), 2000)
        self.assertEquals(grid.price_above(1000), 1000)
        self.assertEquals(grid.price_above(100), 1000)
        
        self.assertRaises(ValueError, grid.price_above, 2100)