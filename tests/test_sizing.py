from pindou.sizing import STANDARD_BOARDS, compute_grid_size


def test_standard_boards_present():
    assert set(STANDARD_BOARDS) == {"15x15", "29x29", "52x52", "52x104"}


def test_square_image_single_square_board():
    board = STANDARD_BOARDS["29x29"]
    g = compute_grid_size(100, 100, board, max_boards_per_axis=3)
    assert g.board_cols == 1 and g.board_rows == 1
    assert g.cols == 29 and g.rows == 29


def test_wide_image_uses_more_columns():
    board = STANDARD_BOARDS["29x29"]
    g = compute_grid_size(300, 100, board, max_boards_per_axis=3)  # 3:1
    assert g.board_cols == 3 and g.board_rows == 1
    assert g.cols == 87 and g.rows == 29


def test_tall_image_uses_more_rows():
    board = STANDARD_BOARDS["29x29"]
    g = compute_grid_size(100, 200, board, max_boards_per_axis=3)  # 1:2
    assert g.board_cols == 1 and g.board_rows == 2


def test_tie_break_prefers_fewer_boards():
    board = STANDARD_BOARDS["29x29"]
    g = compute_grid_size(100, 100, board, max_boards_per_axis=4)
    assert g.board_cols == 1 and g.board_rows == 1  # 不会选 2x2 等更大的同比例解


def test_grid_size_clamped_to_max_beads():
    from pindou.sizing import STANDARD_BOARDS, compute_grid_size
    board = STANDARD_BOARDS["52x104"]
    g = compute_grid_size(1000, 100, board, max_boards_per_axis=10, max_beads=200)
    assert g.cols * g.rows <= 200 * 1.0 + g.board.width * g.board.height
    assert g.board_cols >= 1 and g.board_rows >= 1
