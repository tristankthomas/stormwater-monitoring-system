import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import App from './App.vue'
import router from './router/index.js'

// configure vuetify with dark theme and teal accent
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        colors: {
          primary: '#00BCD4',    // teal - main accent
          secondary: '#26C6DA',
          success: '#66BB6A',    // green - safe readings
          warning: '#FFA726',    // orange - medium pollution
          error: '#EF5350',      // red - high pollution / diverter active
          background: '#0A0E1A', // deep navy background
          surface: '#111827',    // card surface
        }
      }
    }
  }
})

createApp(App)
  .use(vuetify)
  .use(router)
  .mount('#app')