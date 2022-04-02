#!/usr/bin/env python3

from typing import List, Tuple


class Solution:
    # Top left of matrix is 0, 0.
    # Bottom right of matrix is w, h where w = width and h = height.
    #
    # This dictionary contains all valid directions that can be
    # traveled (where each direction is an (x, y) delta). A spiral
    # requires that we move on only one axis at a time.
    next_direction = {
        (1, 0): (0, 1),
        (0, 1): (-1, 0),
        (-1, 0): (0, -1),
        (0, -1): (1, 0),
    }

    def matrix_path(self, width: int, height: int) -> List[Tuple[int, int]]:
        visited_rows = set()
        visited_columns = set()

        # Using "remaining nodes to visit" _feels_ sort of brittle,
        # but it seems to work well. If the pathing code ever gets
        # stuck for some reason, the loop will run forever.
        #
        # Could maybe add an infinite loop check to mitigate that.
        remaining_nodes_to_visit = width * height

        x = -1
        y = 0
        x_direction = 1
        y_direction = 0

        path = list()
        while remaining_nodes_to_visit > 0:
            x += x_direction
            y += y_direction
            x_direction_change = (x >= width) or (x < 0) or (x in visited_columns)
            y_direction_change = (y >= height) or (y < 0) or (y in visited_rows)
            if x_direction_change or y_direction_change:
                x -= x_direction
                y -= y_direction
                if x_direction != 0:
                    visited_rows.add(y)
                elif y_direction != 0:
                    visited_columns.add(x)
                x_direction, y_direction = self.next_direction[(x_direction, y_direction)]
                continue
            remaining_nodes_to_visit -= 1
            path.append((x, y))
        return path

    def spiralOrder(self, matrix: List[List[int]]) -> List[int]:
        matrix_height = len(matrix)
        matrix_width = len(matrix[0])
        return [matrix[y][x] for x, y in self.matrix_path(matrix_width, matrix_height)]


if __name__ == "__main__":
    print(Solution().spiralOrder([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]))
