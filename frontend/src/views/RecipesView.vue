<template>
  <section>
    <div class="page-head">
      <div>
        <h1>Recipes</h1>
        <p class="lede">A small home library. Seeded meals are already here; add your own when you want.</p>
      </div>
      <button class="btn secondary" type="button" @click="startNew">New recipe</button>
    </div>

    <p v-if="error" class="banner error">{{ error }}</p>

    <div class="split">
      <div>
        <label class="field">
          <span>Search</span>
          <input v-model="query" placeholder="Soup, rice, chicken…" @input="search" />
        </label>
        <div class="recipe-list" style="margin-top: 12px">
          <button
            v-for="recipe in recipes"
            :key="recipe.id"
            type="button"
            class="recipe-link"
            :class="{ active: form.id === recipe.id }"
            @click="select(recipe)"
          >
            <strong>{{ recipe.title }}</strong>
            <div>
              <small>{{ recipe.prep_minutes + recipe.cook_minutes }} min · {{ recipe.servings }} servings</small>
            </div>
          </button>
          <p v-if="!recipes.length" class="muted">No recipes match that search.</p>
        </div>
      </div>

      <form class="panel" @submit.prevent="save">
        <h2>{{ form.id ? "Edit recipe" : "New recipe" }}</h2>
        <div class="form-grid" style="margin-top: 12px">
          <label class="field">
            <span>Title</span>
            <input v-model="form.title" required />
          </label>
          <label class="field">
            <span>Description</span>
            <input v-model="form.description" />
          </label>
          <div class="row">
            <label class="field">
              <span>Prep minutes</span>
              <input v-model.number="form.prep_minutes" type="number" min="0" />
            </label>
            <label class="field">
              <span>Cook minutes</span>
              <input v-model.number="form.cook_minutes" type="number" min="0" />
            </label>
            <label class="field">
              <span>Servings</span>
              <input v-model.number="form.servings" type="number" min="1" />
            </label>
          </div>
          <div>
            <span class="field">Tags</span>
            <div class="toggle-row" style="margin-top: 6px">
              <button
                v-for="tag in DIET_TAGS"
                :key="tag.id"
                type="button"
                class="toggle"
                :class="{ on: form.diet_tags.includes(tag.id) }"
                @click="toggleTag(tag.id)"
              >
                {{ tag.label }}
              </button>
            </div>
          </div>
          <div>
            <span>Ingredients</span>
            <div class="stack" style="margin-top: 8px">
              <div v-for="(ingredient, index) in form.ingredients" :key="index" class="ingredient-row">
                <input v-model="ingredient.name" placeholder="Name" />
                <input v-model.number="ingredient.quantity" type="number" min="0.01" step="0.01" placeholder="Qty" />
                <select v-model="ingredient.unit">
                  <option v-for="unit in unitOptions(ingredient.unit)" :key="unit" :value="unit">{{ unit }}</option>
                </select>
                <label class="check">
                  <input v-model="ingredient.optional" type="checkbox" />
                  Optional
                </label>
                <button class="btn ghost small" type="button" @click="removeIngredient(index)" :disabled="form.ingredients.length === 1">
                  Remove
                </button>
              </div>
            </div>
            <button class="btn ghost small" type="button" style="margin-top: 8px" @click="addIngredient">Add ingredient</button>
          </div>
          <label class="field">
            <span>Steps, one per line</span>
            <textarea v-model="steps" />
          </label>
        </div>
        <div class="actions" style="margin-top: 14px">
          <button class="btn" type="submit">{{ form.id ? "Save recipe" : "Create recipe" }}</button>
          <button v-if="form.id" class="btn ghost" type="button" @click="remove">Delete</button>
        </div>
      </form>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { api } from "../api";
import { DIET_TAGS, UNITS } from "../constants";

const recipes = ref([]);
const query = ref("");
const error = ref("");
const steps = ref("");
const form = reactive(blank());

function blank() {
  return {
    id: null,
    title: "",
    description: "",
    prep_minutes: 10,
    cook_minutes: 15,
    servings: 2,
    diet_tags: [],
    ingredients: [{ name: "", quantity: 1, unit: "piece", optional: false }],
  };
}

function unitOptions(current) {
  if (current && !UNITS.includes(current)) return [current, ...UNITS];
  return UNITS;
}

function startNew() {
  Object.assign(form, blank());
  form.diet_tags = [];
  form.ingredients = [{ name: "", quantity: 1, unit: "piece", optional: false }];
  steps.value = "";
}

function select(recipe) {
  form.id = recipe.id;
  form.title = recipe.title;
  form.description = recipe.description || "";
  form.prep_minutes = recipe.prep_minutes;
  form.cook_minutes = recipe.cook_minutes;
  form.servings = recipe.servings;
  form.diet_tags = [...(recipe.diet_tags || [])];
  form.ingredients = (recipe.ingredients || []).map((item) => ({
    name: item.name,
    quantity: item.quantity,
    unit: item.unit || "piece",
    optional: Boolean(item.optional),
  }));
  if (!form.ingredients.length) addIngredient();
  steps.value = (recipe.instructions || []).join("\n");
}

function addIngredient() {
  form.ingredients.push({ name: "", quantity: 1, unit: "piece", optional: false });
}

function removeIngredient(index) {
  form.ingredients.splice(index, 1);
}

function toggleTag(id) {
  if (form.diet_tags.includes(id)) {
    form.diet_tags = form.diet_tags.filter((tag) => tag !== id);
    if (id === "vegetarian") form.diet_tags = form.diet_tags.filter((tag) => tag !== "vegan");
    return;
  }
  form.diet_tags = [...form.diet_tags, id];
  if (id === "vegan" && !form.diet_tags.includes("vegetarian")) {
    form.diet_tags = [...form.diet_tags, "vegetarian"];
  }
}

function toPayload() {
  return {
    title: form.title,
    description: form.description,
    prep_minutes: Number(form.prep_minutes) || 0,
    cook_minutes: Number(form.cook_minutes) || 0,
    servings: Number(form.servings) || 1,
    diet_tags: form.diet_tags,
    ingredients: form.ingredients
      .filter((item) => item.name.trim())
      .map((item) => ({
        name: item.name.trim(),
        quantity: item.quantity || null,
        unit: item.unit || null,
        optional: Boolean(item.optional),
      })),
    instructions: steps.value.split("\n").map((line) => line.trim()).filter(Boolean),
  };
}

async function refresh() {
  recipes.value = await api.recipes.list(query.value.trim());
}

let searchTimer;
function search() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    refresh().catch((err) => {
      error.value = err.message;
    });
  }, 200);
}

async function save() {
  error.value = "";
  const payload = toPayload();
  if (!payload.ingredients.length) {
    error.value = "Add at least one ingredient.";
    return;
  }
  try {
    const saved = form.id ? await api.recipes.update(form.id, payload) : await api.recipes.create(payload);
    await refresh();
    select(saved);
  } catch (err) {
    error.value = err.message || "Could not save the recipe.";
  }
}

async function remove() {
  if (!form.id || !window.confirm(`Delete ${form.title}?`)) return;
  try {
    await api.recipes.remove(form.id);
    startNew();
    await refresh();
  } catch (err) {
    error.value = err.message || "Could not delete the recipe.";
  }
}

onMounted(async () => {
  try {
    await refresh();
  } catch (err) {
    error.value = err.message || "The API is not reachable.";
  }
});
</script>
