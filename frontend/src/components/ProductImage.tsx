import { useId, useState } from 'react'
import type { Product } from '../types'

const illustrations: Record<string, { colors: [string, string]; shape: 'bottle' | 'tube' | 'jar' | 'dropper' }> = {
  cleanser: { colors: ['#b9d9c1', '#edf5e8'], shape: 'bottle' },
  'face wash': { colors: ['#a9cdbb', '#e5f1e8'], shape: 'tube' },
  moisturizer: { colors: ['#a9c2df', '#edf3fb'], shape: 'jar' },
  sunscreen: { colors: ['#e8b58d', '#fff1dd'], shape: 'tube' },
  serum: { colors: ['#bea1d6', '#f4eaf8'], shape: 'dropper' },
  'acne care': { colors: ['#d69e90', '#faeae4'], shape: 'bottle' },
  toner: { colors: ['#9cbfbe', '#e8f3f0'], shape: 'bottle' },
  'dark spot care': { colors: ['#d4ad68', '#fbf0d9'], shape: 'dropper' },
  'eye care': { colors: ['#c5b98a', '#f6f0dc'], shape: 'tube' },
  'lip care': { colors: ['#cf96a9', '#f8e8ee'], shape: 'jar' },
  'body care': { colors: ['#a7be91', '#ebf2df'], shape: 'bottle' },
}

export default function ProductImage({ product, className }: { product: Product; className: string }) {
  const id = useId().replaceAll(':', '')
  const [failed, setFailed] = useState(false)
  const source = product.image_url?.trim()
  if (source && !failed) {
    return <img className={className} src={source} alt={`Product image for ${product.name}`} loading="lazy" onError={() => setFailed(true)} />
  }

  const illustration = illustrations[product.category.toLowerCase()] ?? { colors: ['#9eb9a0', '#eef3e8'] as [string, string], shape: 'bottle' as const }
  const { colors, shape } = illustration
  const title = product.name.replace(/\s*\(Demo\)/i, '')

  return (
    <svg className={className} viewBox="0 0 360 240" role="img" aria-label={`Illustration of ${product.name}`}>
      <defs>
        <linearGradient id={`product-bg-${id}`} x1="0" y1="0" x2="1" y2="1">
          <stop stopColor={colors[0]} stopOpacity=".24" />
          <stop offset="1" stopColor={colors[1]} />
        </linearGradient>
        <linearGradient id={`product-pack-${id}`} x1="0" y1="0" x2="1" y2="1">
          <stop stopColor="#fff" />
          <stop offset="1" stopColor={colors[1]} />
        </linearGradient>
        <filter id={`product-shadow-${id}`} x="-40%" y="-25%" width="180%" height="170%">
          <feDropShadow dx="0" dy="9" stdDeviation="8" floodColor="#2d4434" floodOpacity=".16" />
        </filter>
      </defs>
      <rect width="360" height="240" fill={`url(#product-bg-${id})`} />
      <circle cx="285" cy="45" r="80" fill={colors[0]} opacity=".16" />
      <circle cx="65" cy="213" r="95" fill={colors[0]} opacity=".12" />
      <ellipse cx="180" cy="205" rx="79" ry="11" fill="#46574a" opacity=".12" />
      <g filter={`url(#product-shadow-${id})`}>
        {shape === 'bottle' && <>
          <rect x="158" y="46" width="44" height="22" rx="5" fill={colors[0]} />
          <rect x="151" y="65" width="58" height="17" rx="4" fill={colors[1]} stroke="#fff" strokeOpacity=".8" />
          <rect x="131" y="78" width="98" height="119" rx="20" fill={`url(#product-pack-${id})`} stroke="#fff" strokeWidth="2" />
        </>}
        {shape === 'tube' && <>
          <path d="M145 58 Q180 47 215 58 L207 185 Q180 199 153 185 Z" fill={`url(#product-pack-${id})`} stroke="#fff" strokeWidth="2" />
          <path d="M145 58 Q180 48 215 58 L213 76 Q180 84 147 76 Z" fill={colors[0]} opacity=".8" />
          <rect x="165" y="184" width="30" height="13" rx="4" fill={colors[0]} />
        </>}
        {shape === 'jar' && <>
          <rect x="137" y="91" width="86" height="16" rx="5" fill={colors[0]} />
          <rect x="132" y="105" width="96" height="81" rx="17" fill={`url(#product-pack-${id})`} stroke="#fff" strokeWidth="2" />
          <path d="M136 120 Q180 128 224 120" fill="none" stroke={colors[0]} strokeOpacity=".45" strokeWidth="2" />
        </>}
        {shape === 'dropper' && <>
          <rect x="169" y="47" width="22" height="28" rx="5" fill={colors[0]} />
          <rect x="173" y="30" width="14" height="22" rx="7" fill={colors[0]} />
          <rect x="151" y="72" width="58" height="15" rx="4" fill={colors[1]} stroke="#fff" />
          <rect x="137" y="84" width="86" height="110" rx="17" fill={`url(#product-pack-${id})`} stroke="#fff" strokeWidth="2" />
        </>}
        <rect x="144" y={shape === 'jar' ? 128 : 112} width="72" height="49" rx="6" fill="#fff" fillOpacity=".76" />
        <path d="M158 126h44" stroke={colors[0]} strokeWidth="3" strokeLinecap="round" />
        <text x="180" y="144" textAnchor="middle" fill="#354a3a" fontSize="7" fontWeight="700" letterSpacing="1.2">DERMACARE</text>
        <text x="180" y="157" textAnchor="middle" fill="#657669" fontSize="6">{title.length > 19 ? `${title.slice(0, 17)}…` : title}</text>
        <text x="180" y="168" textAnchor="middle" fill="#87958a" fontSize="5" letterSpacing="1">SKIN CARE</text>
      </g>
      <text x="180" y="226" textAnchor="middle" fill="#65776a" fontSize="8" fontWeight="700" letterSpacing="1.4">ILLUSTRATIVE DEMO PRODUCT</text>
    </svg>
  )
}
