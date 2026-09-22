<template>
  <section>
    <div class="page-head">
      <div>
        <h1>Pantry</h1>
        <p class="lede">What is actually in the kitchen. Quantity and expiry make the ranking sharper.</p>
      </div>
      <button class="btn secondary" @click="loadSample">Load sample pantry</button>
    </div>

    <p v-if="error" class="banner error">{{ error }}</p>
    <p v-if="notice" class="banner ok">{{ notice }}</p>

    <form class="panel" @submit.prevent="save">
      <div class="row">
        <label class="field grow">
          <span>Item</span>
          <input v-model="form.name" required placeholder="Canned tomatoes" />
        </label>
        <label class="field">
          <span>Quantity</span>
          <input v-model.number="form.quantity" type="number" min="0.01" step="0.01" required />
        </label>
        <label class="field">
          <span>Unit</span>
          <select v-model="form.unit">
            <option v-for="unit in UNITS" :key="unit" :value="unit">{{ unit }}</option>
          </select>
        </label>
        <label class="field">
          <span>Expiry</span>
          <input v-model="form.expires_on" type="date" />
        </label>
      </div>
      <div class="actions" style="margin-top: 12px">
        <button class="btn" type="submit">{{ form.id ? "Save changes" : "Add item" }}</button>
        <button v-if="form.id" class="btn ghost" type="button" @click="reset">Cancel</button>
      </div>
    </form>

    <div class="stack" style="margin-top: 16px">
      <p v-if="!items.length" class="banner">Nothing stored yet. Add an item or load the sample pantry.</p>
      <article v-for="item in items" :key="item.id" class="pantry-item">
        <div>
          <strong>{{ item.name }}</strong>
          <div class="muted">
            {{ formatAmount(item.quantity, item.unit) }}
            <template v-if="item.expires_on"> · use by {{ formatDate(item.expires_on) }}</template>
          </div>
        </div>
        <div class="actions">
          <button class="btn ghost small" type="button" @click="edit(item)">Edit</button>
          <button class="btn ghost small" type="button" @click="remove(item)">Remove</button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { UNITS, formatAmount, formatDate } from "../constants";

const router = useRouter();
const items = ref([]);
const error = ref("");
const notice = ref("");
const form = reactive({ id: null, name: "", quantity: 1, unit: "piece", expires_on: "" });

function reset() {
  form.id = null;
  form.name = "";
  form.quantity = 1;
  form.unit = "piece";
  form.expires_on = "";
}

function payload() {
  return {
    name: form.name,
    quantity: Number(form.quantity),
    unit: form.unit,
    expires_on: form.expires_on || null,
  };
}

async function refresh() {
  items.value = await api.pantry.list();
}

async function save() {
  error.value = "";
  notice.value = "";
  try {
    if (form.id) await api.pantry.update(form.id, payload());
    else await api.pantry.create(payload());
    reset();
    await refresh();
  } catch (err) {
    error.value = err.message || "Could not save that item.";
  }
}

function edit(item) {
  form.id = item.id;
  form.name = item.name;
  form.quantity = item.quantity;
  form.unit = item.unit;
  form.expires_on = item.expires_on || "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function remove(item) {
  if (!window.confirm(`Remove ${item.name} from the pantry?`)) return;
  error.value = "";
  try {
    await api.pantry.remove(item.id);
    if (form.id === item.id) reset();
    await refresh();
  } catch (err) {
    error.value = err.message || "Could not remove that item.";
  }
}

async function loadSample() {
  error.value = "";
  notice.value = "";
  try {
    items.value = await api.pantry.sample();
    notice.value = "Sample pantry loaded.";
    router.push({ path: "/", query: { cook: "1" } });
  } catch (err) {
    error.value = err.message || "Could not load the sample pantry.";
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
