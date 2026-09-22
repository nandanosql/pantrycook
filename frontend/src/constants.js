export const DIET_TAGS = [
  { id: "vegetarian", label: "Vegetarian" },
  { id: "vegan", label: "Vegan" },
  { id: "pescatarian", label: "Pescatarian" },
  { id: "gluten-free", label: "Gluten-free" },
  { id: "dairy-free", label: "Dairy-free" },
];

export const UNITS = ["g", "kg", "ml", "l", "cup", "tbsp", "tsp", "piece", "clove", "can", "bunch", "slice", "head"];

export function dietLabel(id) {
  return DIET_TAGS.find((tag) => tag.id === id)?.label || id;
}

export function formatQty(value) {
  if (value == null || value === "") return "";
  const number = Number(value);
  if (Number.isNaN(number)) return String(value);
  if (Number.isInteger(number)) return String(number);
  return String(Math.round(number * 100) / 100);
}

export function formatAmount(quantity, unit) {
  const qty = formatQty(quantity);
  if (!qty) return unit || "";
  return unit ? `${qty} ${unit}` : qty;
}

export function formatDate(value) {
  if (!value) return "";
  const [year, month, day] = String(value).slice(0, 10).split("-");
  if (!year || !month || !day) return value;
  const date = new Date(Number(year), Number(month) - 1, Number(day));
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
