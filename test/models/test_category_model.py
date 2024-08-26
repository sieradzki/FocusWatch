import unittest
from focuswatch.models.category import Category


class TestCategory(unittest.TestCase):

  def setUp(self):
    self.category = Category(
      id=1, name="Work", parent_category_id=None, color="#00cc00")

  def test_category_initialization(self):
    """Test that the Category is initialized correctly."""
    self.assertEqual(self.category.id, 1)
    self.assertEqual(self.category.name, "Work")
    self.assertIsNone(self.category.parent_category_id)
    self.assertEqual(self.category.color, "#00cc00")

  def test_category_with_valid_color_hex(self):
    """Test that a category with a valid hex color is accepted."""
    category = Category(name="Audio", color="#ABCDEF")
    self.assertEqual(category.color, "#ABCDEF")

  def test_category_with_valid_color_rgb(self):
    """Test that a category with a valid rgb color is accepted."""
    category = Category(name="Work", color="rgb(0,204,0)")
    self.assertEqual(category.color, "rgb(0,204,0)")

  def test_category_with_invalid_color(self):
    """Test that an invalid color format raises a ValueError."""
    with self.assertRaises(ValueError):
      Category(name="InvalidColor", color="notacolor")

  def test_category_with_invalid_rgb_color(self):
    """Test that an invalid RGB color format raises a ValueError."""
    with self.assertRaises(ValueError):
      Category(name="InvalidRGB", color="rgb(256,0,0)")

    with self.assertRaises(ValueError):
      Category(name="InvalidRGB", color="rgb(0,-2,0)")

  def test_category_with_self_as_parent(self):
    """Test that a category cannot be its own parent."""
    with self.assertRaises(ValueError):
      Category(id=1, name="SelfParent", parent_category_id=1)

  def test_is_root_category(self):
    """Test that is_root_category property returns True for root categories."""
    self.assertTrue(self.category.is_root_category)
    non_root_category = Category(name="Subcategory", parent_category_id=1)
    self.assertFalse(non_root_category.is_root_category)


if __name__ == '__main__':
  unittest.main()
