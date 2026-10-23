import { h } from 'vue'

// ikon garis 24x24, warnanya ikut currentColor. dirender lewat h() supaya tidak perlu v-html
const c = (cx, cy, r) => ['circle', { cx, cy, r }]
const p = (d) => ['path', { d }]
const r = (x, y, width, height, rx = 0) => ['rect', { x, y, width, height, rx }]

const IKON = {
  // olahraga
  tennis: [c(12, 12, 9), p('M6 4.6c2.4 2 3.6 4.5 3.6 7.4s-1.2 5.4-3.6 7.4'), p('M18 4.6c-2.4 2-3.6 4.5-3.6 7.4s1.2 5.4 3.6 7.4')],
  padel: [
    p('M10 2.8c3.6 0 6.2 2.7 6.2 6.2 0 3.4-2.6 6-6.2 6S3.8 12.4 3.8 9c0-3.5 2.6-6.2 6.2-6.2z'),
    p('M14.2 13.4 20.5 19.7'),
    c(8, 7.5, 0.6),
    c(12, 7.5, 0.6),
    c(10, 10.5, 0.6),
    c(19, 5, 1.8),
  ],
  futsal: [
    c(12, 12, 9),
    p('M12 8.2l3.4 2.5-1.3 4h-4.2l-1.3-4z'),
    p('M12 8.2V3.2M15.4 10.7l4.6-1.6M14.1 14.7l2.7 4M9.9 14.7l-2.7 4M8.6 10.7 4 9.1'),
  ],
  golf_driving: [p('M7 21V3l9 3.6L7 10.2'), c(16.5, 17.5, 2.4), p('M3 21h8')],
  badminton: [c(12, 18.6, 2.6), p('M9.6 17.2 6 3.5h12l-3.6 13.7'), p('M10.4 3.5l.9 13M13.6 3.5l-.9 13M7.2 8h9.6')],
  voli: [c(12, 12, 9), p('M12 3c1.8 3 2 6.2 0 9'), p('M12 12c3.3.3 6 1.9 7.8 4.5'), p('M12 12c-1.8 2.8-4.6 4.4-7.8 4.5'), p('M5 6.5c3 .3 5.4 2.1 7 5.5')],
  basket: [c(12, 12, 9), p('M12 3v18M3 12h18'), p('M5.6 5.6c2.6 2.8 2.6 10 0 12.8M18.4 5.6c-2.6 2.8-2.6 10 0 12.8')],

  // antarmuka
  menu: [p('M4 6h16M4 12h16M4 18h16')],
  sun: [c(12, 12, 4), p('M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4')],
  moon: [p('M20.5 13.2A8.5 8.5 0 1 1 10.8 3.5a6.6 6.6 0 0 0 9.7 9.7z')],
  search: [c(11, 11, 7), p('M20 20l-3.8-3.8')],
  chart: [p('M4 20h16'), p('M6.5 20v-8M12 20V5M17.5 20v-5')],
  inbox: [p('M22 12h-6l-2 3h-4l-2-3H2'), p('M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.7 4H7.3a2 2 0 0 0-1.8 1.1z')],
  calendar: [r(3, 4.5, 18, 16.5, 2), p('M16 2.5v4M8 2.5v4M3 10h18')],
  court: [r(3, 5, 18, 14, 1.5), p('M12 5v14'), c(12, 12, 2.6)],
  clock: [c(12, 12, 9), p('M12 7v5l3.2 2')],
  sliders: [p('M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1.5 14h5M9.5 8h5M17.5 16h5')],
  'chevron-left': [p('M15 18l-6-6 6-6')],
  'chevron-right': [p('M9 18l6-6-6-6')],
  close: [p('M18 6 6 18M6 6l12 12')],
  check: [p('M20 6 9 17l-5-5')],
  alert: [c(12, 12, 9), p('M12 7.5v5M12 16.2v.3')],
  info: [c(12, 12, 9), p('M12 16v-4.5M12 7.8v.3')],
  'map-pin': [p('M12 21s-7-6.1-7-11.2a7 7 0 0 1 14 0C19 14.9 12 21 12 21z'), c(12, 9.8, 2.4)],
  users: [
    c(9, 7, 4),
    p('M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2'),
    p('M16 3.13a4 4 0 0 1 0 7.75'),
    p('M21 21v-2a4 4 0 0 0-3-3.85'),
  ],
}

export default {
  name: 'AppIcon',
  props: {
    name: { type: String, required: true },
    size: { type: [Number, String], default: 20 },
    stroke: { type: [Number, String], default: 2 },
  },
  setup(props) {
    return () =>
      h(
        'svg',
        {
          class: 'ikon-svg',
          width: props.size,
          height: props.size,
          viewBox: '0 0 24 24',
          fill: 'none',
          stroke: 'currentColor',
          'stroke-width': props.stroke,
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          'aria-hidden': 'true',
          focusable: 'false',
        },
        (IKON[props.name] || IKON.court).map(([tag, attrs]) => h(tag, attrs)),
      )
  },
}
