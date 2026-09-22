<template>
  <div class="app">
    <header class="topbar">
      <router-link class="brand" to="/">
        <svg class="logo" viewBox="0 0 32 32" aria-hidden="true">
          <path d="M7 14h18v8a4 4 0 0 1-4 4H11a4 4 0 0 1-4-4v-8z" fill="none" stroke="currentColor" stroke-width="2" />
          <path d="M11 14c0-3 10-3 10 0" fill="none" stroke="currentColor" stroke-width="2" />
          <path d="M17 8c2.2-3.2 6-2 4.6 1.2" fill="none" stroke="#e7a06a" stroke-width="2" stroke-linecap="round" />
        </svg>
        <span>
          <strong>PantryCook</strong>
          <small>Cook from what you have.</small>
        </span>
      </router-link>
      <nav>
        <router-link to="/">Tonight</router-link>
        <router-link to="/pantry">Pantry</router-link>
        <router-link to="/recipes">Recipes</router-link>
        <router-link to="/settings">Settings</router-link>
      </nav>
    </header>
    <main>
      <router-view />
    </main>
    <footer class="site">PantryCook v0.1 · single-user · self-hosted · by Nandan Priyadarshi</footer>
  </div>
</template>
