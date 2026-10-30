import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { Bot, ChevronDown, LoaderCircle, MessageCircle, Send, Sparkles, Upload, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { errorMessage, productApi, skinApi } from './services/api'
import ProductImage from './components/ProductImage'
import type { Analysis, Product } from './types'

type ChatAnswers = {
  skin_type: string
  budget: string
  sensitivity: string
  preferences: string[]
  concerns: string[]
}

type Message = {
  id: number
  from: 'assistant' | 'user'
  text: string
  analysis?: Analysis
  products?: Product[]
}

const questions = [
  { key: 'skin_type', prompt: 'How would you describe your skin most days?', options: ['Dry', 'Oily', 'Combination', 'Sensitive', 'Normal'] },
  { key: 'budget', prompt: 'What budget feels comfortable for one product?', options: ['Under ₹500', '₹500 - ₹1,500', '₹1,500 - ₹3,000', '₹3,000+'] },
  { key: 'sensitivity', prompt: 'Does your skin tend to react or feel irritated?', options: ['Yes, sensitive', 'No, not sensitive'] },
  { key: 'preferences', prompt: 'Any product preferences? Choose as many as you like.', options: ['fragrance_free', 'vegan', 'cruelty_free'] },
  { key: 'concerns', prompt: 'What would you like your routine to focus on?', options: ['acne', 'dark spots', 'dryness', 'oiliness', 'redness', 'texture'] },
] as const

const budgetCap: Record<string, number> = {
  'Under ₹500': 500,
  '₹500 - ₹1,500': 1500,
  '₹1,500 - ₹3,000': 3000,
  '₹3,000+': 10000,
}

const emptyAnswers: ChatAnswers = { skin_type: '', budget: '', sensitivity: '', preferences: [], concerns: [] }

function makeMessage(from: Message['from'], text: string, extra: Partial<Message> = {}): Message {
  return { id: Date.now() + Math.random(), from, text, ...extra }
}

function rankProducts(products: Product[], answers: ChatAnswers, analysis: Analysis | null) {
  const observed = Object.entries(analysis?.observations ?? {})
    .filter(([, value]) => Number(value?.score ?? 0) >= 0.45)
    .map(([key]) => key)
  const budget = budgetCap[answers.budget] ?? Number.MAX_SAFE_INTEGER

  return products.map((product) => {
    let score = 0
    const skinTypes = product.skin_types.map((item) => item.toLowerCase())
    const skinType = answers.skin_type.toLowerCase()
    if (skinTypes.includes(skinType) || skinTypes.includes('all')) score += 22
    if (product.price <= budget) score += 18
    if (answers.sensitivity === 'Yes, sensitive' && product.suitable_for_sensitive_skin) score += 16
    if (answers.preferences.includes('fragrance_free') && product.fragrance_free) score += 12
    if (answers.preferences.includes('vegan') && product.vegan) score += 12
    if (answers.preferences.includes('cruelty_free') && product.cruelty_free) score += 12
    if (answers.concerns.some((concern) => product.concerns.some((item) => item.toLowerCase().includes(concern.replace(' ', '_')) || concern.includes(item.toLowerCase())))) score += 18
    if (observed.some((key) => product.concerns.some((concern) => concern.toLowerCase().includes(key.replace('_', ' '))))) score += 16

    const reasons: string[] = []
    if (product.price <= budget) reasons.push('Fits your budget')
    if (skinTypes.includes(skinType)) reasons.push(`Suitable for ${answers.skin_type} skin`)
    if (product.fragrance_free && answers.preferences.includes('fragrance_free')) reasons.push('Fragrance-free')
    if (product.suitable_for_sensitive_skin && answers.sensitivity === 'Yes, sensitive') reasons.push('Suitable for sensitive skin')
    return { ...product, match_score: Math.min(99, score), reasons }
  }).filter((product) => (product.match_score ?? 0) >= 25)
    .sort((a, b) => (b.match_score ?? 0) - (a.match_score ?? 0))
    .slice(0, 4)
}

function ProductSuggestion({ product }: { product: Product }) {
  return (
    <article className="assistant-product">
      <ProductImage product={product} className="assistant-product-image" />
      <div className="assistant-product-heading">
        <span>{product.brand} · {product.category}</span>
        {product.match_score !== undefined && <b>{product.match_score}% match</b>}
      </div>
      <strong>{product.name}</strong>
      <p>{product.description}</p>
      <div className="assistant-product-meta"><b>₹{product.price}</b><span>★ {product.rating ?? 4.8}</span></div>
      {product.reasons?.length ? <small>{product.reasons.slice(0, 2).join(' · ')}</small> : null}
      <div className="assistant-product-links">
        {product.amazon_url && <a href={product.amazon_url} target="_blank" rel="noreferrer">Amazon</a>}
        {product.flipkart_url && <a href={product.flipkart_url} target="_blank" rel="noreferrer">Flipkart</a>}
      </div>
    </article>
  )
}

export default function AssistantWidget({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const { user } = useAuth()
  const [messages, setMessages] = useState<Message[]>([
    makeMessage('assistant', 'Hi! I’m your skincare guide. I can analyze an image, learn what you’re looking for, and suggest products from the catalog. What would you like to do?'),
  ])
  const [phase, setPhase] = useState<'welcome' | 'questions' | 'results'>('welcome')
  const [questionIndex, setQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<ChatAnswers>(emptyAnswers)
  const [selected, setSelected] = useState<string[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [typing, setTyping] = useState(false)
  const [busy, setBusy] = useState(false)
  const [draft, setDraft] = useState('')
  const [catalogError, setCatalogError] = useState('')
  const [error, setError] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)
  const messageList = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!user) {
      setProducts([])
      return
    }
    productApi.list().then(setProducts).catch((failure: unknown) => setCatalogError(errorMessage(failure)))
  }, [user])

  useEffect(() => {
    if (messageList.current) messageList.current.scrollTop = messageList.current.scrollHeight
  }, [messages, typing, open])

  const recommendations = useMemo(() => rankProducts(products, answers, analysis), [analysis, answers, products])

  function reply(text: string, extra: Partial<Message> = {}) {
    setTyping(true)
    window.setTimeout(() => {
      setMessages((previous) => [...previous, makeMessage('assistant', text, extra)])
      setTyping(false)
    }, Math.min(850, Math.max(320, text.length * 9)))
  }

  function startQuestions() {
    setPhase('questions')
    setQuestionIndex(0)
    setAnswers(emptyAnswers)
    setSelected([])
    setAnalysis(null)
    setMessages((previous) => [...previous, makeMessage('user', 'Help me build a routine')])
    reply(questions[0].prompt)
  }

  function showInfo(topic: 'type' | 'budget' | 'products') {
    const text = topic === 'type'
      ? 'Skin types are a useful starting point, not a diagnosis. After cleansing, notice how your skin feels: tight or flaky can point to dry; shiny across most areas can point to oily; an oily T-zone with drier cheeks often feels combination. If you are unsure, choose “Not sure” in your profile and we can keep suggestions gentle.'
      : topic === 'budget'
        ? 'A simple routine can stay affordable: start with a gentle cleanser, moisturizer, and daytime sunscreen. You do not need many active ingredients at once. Tell me your comfortable per-product budget and I’ll prioritize catalog items around it.'
        : 'I can narrow down the product catalog using your skin type, budget, sensitivities, preferences, and concerns. Start a quick profile and I’ll show the best matches here in the chat.'
    setMessages((previous) => [...previous, makeMessage('user', topic === 'type' ? 'How do I figure out my skin type?' : topic === 'budget' ? 'Give me budget-friendly advice' : 'Show me product recommendations')])
    reply(text)
  }

  function submitAnswer(value: string) {
    const question = questions[questionIndex]
    if (!question || !value.trim() || typing) return
    const answer = value.trim()
    const displayedAnswer = question.key === 'preferences' || question.key === 'concerns'
      ? answer.split(',').map((item) => item.trim().replaceAll('_', ' ').replace(/\b\w/g, (character) => character.toUpperCase())).join(', ')
      : answer
    setMessages((previous) => [...previous, makeMessage('user', displayedAnswer)])
    const nextAnswers = { ...answers }
    if (question.key === 'preferences' || question.key === 'concerns') {
      nextAnswers[question.key] = answer.split(',').map((item) => item.trim()).filter(Boolean)
    } else {
      nextAnswers[question.key] = answer
    }
    setAnswers(nextAnswers)
    setSelected([])
    setDraft('')

    if (questionIndex < questions.length - 1) {
      const nextIndex = questionIndex + 1
      setQuestionIndex(nextIndex)
      reply(questions[nextIndex].prompt)
      return
    }

    setPhase('results')
    reply(recommendations.length
      ? 'Thanks, I’ve matched your answers with the catalog. Here are a few options to explore.'
      : catalogError || 'Thanks, I’ve saved your preferences in this chat. I could not find product matches right now, but you can try adjusting your budget or focus.',
    { products: rankProducts(products, nextAnswers, analysis) })
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = draft.trim()
    if (!value || typing || busy) return
    if (phase === 'questions') {
      submitAnswer(value)
      return
    }
    setMessages((previous) => [...previous, makeMessage('user', value)])
    setDraft('')
    const normalized = value.toLowerCase()
    if (normalized.includes('budget') || normalized.includes('cheap') || normalized.includes('afford')) showFreeReply('budget')
    else if (normalized.includes('skin type') || normalized.includes('oily') || normalized.includes('dry skin')) showFreeReply('type')
    else if (normalized.includes('product') || normalized.includes('recommend')) showFreeReply('products')
    else reply(user
      ? 'I can help you build a skin profile, analyze a photo, or narrow down product ideas. Choose one of the quick options below, or tell me your skin type and budget to get started.'
      : 'I can explain skincare basics now. To analyze an image or get personalized product matches, please sign in first.')
  }

  function showFreeReply(topic: 'type' | 'budget' | 'products') {
    const text = topic === 'type'
      ? 'Skin types are a guide, not a diagnosis. Notice how your skin feels a little while after cleansing: tightness may suggest dryness, shine across most areas may suggest oiliness, and an oily T-zone with drier cheeks may suggest combination skin.'
      : topic === 'budget'
        ? 'A gentle cleanser, moisturizer, and daytime sunscreen are a good simple starting point. You can set a per-product budget in the profile questions and I’ll rank catalog matches within it.'
        : 'I can compare catalog products with your preferences. Start a quick skin profile and I’ll show matching products here without sending you to another page.'
    reply(text)
  }

  async function analyzePhoto(file: File | undefined) {
    if (!file) return
    if (!user) {
      setMessages((previous) => [...previous, makeMessage('assistant', 'Image analysis is available after you sign in. Your photo is analyzed by the app’s image service and should not be treated as a medical diagnosis.')])
      return
    }
    setError('')
    setBusy(true)
    setMessages((previous) => [...previous, makeMessage('user', `Analyze this photo: ${file.name}`)])
    setTyping(true)
    try {
      const result = await skinApi.analyze(file)
      setAnalysis(result)
      setMessages((previous) => [...previous, makeMessage(
        'assistant',
        `The image analysis is complete. The estimated skin type is ${result.skin_type_estimate.replaceAll('_', ' ')} (${Math.round((result.confidence || 0) * 100)}% confidence). These are image-based observations, not a diagnosis. Want me to use them to tailor product ideas?`,
        { analysis: result },
      )])
    } catch (failure) {
      const message = errorMessage(failure)
      setError(message)
      setMessages((previous) => [...previous, makeMessage('assistant', `I couldn’t analyze that image: ${message}`)])
    } finally {
      setTyping(false)
      setBusy(false)
      if (fileInput.current) fileInput.current.value = ''
    }
  }

  function startOver() {
    setPhase('welcome')
    setQuestionIndex(0)
    setAnswers(emptyAnswers)
    setSelected([])
    setAnalysis(null)
    setError('')
    setMessages([makeMessage('assistant', 'Let’s start fresh. I can analyze an image, help build a routine, or answer a skincare question.')])
  }

  const activeQuestion = phase === 'questions' ? questions[questionIndex] : null
  const multiChoice = activeQuestion?.key === 'preferences' || activeQuestion?.key === 'concerns'

  return (
    <div className="assistant-widget">
      {open && (
        <section className="assistant-panel" aria-label="Skincare assistant" role="dialog" aria-modal="false">
          <header className="assistant-header">
            <span className="assistant-avatar"><Bot size={20} /></span>
            <div className="assistant-title"><strong>Skin care assistant</strong><span><i /> {typing || busy ? 'Thinking…' : 'Here to help'}</span></div>
            <button type="button" className="assistant-header-button" onClick={startOver} aria-label="Start a new conversation"><Sparkles size={16} /></button>
            <button type="button" className="assistant-header-button" onClick={() => onOpenChange(false)} aria-label="Close assistant"><X size={18} /></button>
          </header>

          <div className="assistant-message-list" ref={messageList} aria-live="polite">
            {messages.map((message) => (
              <div className={`assistant-message ${message.from}`} key={message.id}>
                {message.from === 'assistant' && <span className="assistant-message-avatar"><Bot size={14} /></span>}
                <div className="assistant-bubble">
                  <p>{message.text}</p>
                  {message.analysis && (
                    <div className="assistant-insight">
                      <strong>{message.analysis.skin_type_estimate.replaceAll('_', ' ')}</strong>
                      <span>{Math.round((message.analysis.confidence || 0) * 100)}% confidence</span>
                      <div>{Object.entries(message.analysis.observations ?? {}).slice(0, 3).map(([key, value]) => <small key={key}>{key.replaceAll('_', ' ')} · {value.severity}</small>)}</div>
                    </div>
                  )}
                  {message.products?.map((product) => <ProductSuggestion key={product.id} product={product} />)}
                </div>
              </div>
            ))}
            {typing && <div className="assistant-message"><span className="assistant-message-avatar"><Bot size={14} /></span><div className="assistant-typing" aria-label="Assistant is typing"><i /><i /><i /></div></div>}
            {busy && <div className="assistant-working"><LoaderCircle size={14} /> Analyzing your image…</div>}
          </div>

          <div className="assistant-actions">
            {phase === 'welcome' && (
              <div className="assistant-quick-actions">
                <button type="button" onClick={() => user ? fileInput.current?.click() : setMessages((previous) => [...previous, makeMessage('assistant', 'Please sign in to use image analysis. Your skin image is sent securely to the app’s analysis API and is not a medical diagnosis.')])}><Upload size={14} /> Analyze a photo</button>
                <button type="button" onClick={startQuestions}>Build my routine <ChevronDown size={14} /></button>
                <button type="button" onClick={() => showInfo('type')}>Skin type help</button>
                <button type="button" onClick={() => showInfo('budget')}>Budget tips</button>
              </div>
            )}
            {activeQuestion && (
              <>
                <div className="assistant-progress">QUESTION {questionIndex + 1} OF {questions.length}</div>
                <div className="assistant-option-list">
                  {activeQuestion.options.map((option) => {
                    const label = option.replaceAll('_', ' ').replace(/\b\w/g, (character) => character.toUpperCase())
                    const isSelected = multiChoice ? selected.includes(option) : false
                    return <button type="button" key={option} className={isSelected ? 'selected' : ''} disabled={typing} onClick={() => {
                      if (multiChoice) setSelected((current) => current.includes(option) ? current.filter((item) => item !== option) : [...current, option])
                      else submitAnswer(option)
                    }}>{label}</button>
                  })}
                </div>
                {multiChoice && <button type="button" className="assistant-continue" disabled={typing} onClick={() => submitAnswer(selected.join(', ') || 'No preference')}>Continue <Send size={13} /></button>}
              </>
            )}
            {phase === 'results' && (
              <div className="assistant-result-tools">
                <button type="button" onClick={startQuestions}>Update my answers</button>
                <button type="button" onClick={() => fileInput.current?.click()}>Add a photo</button>
              </div>
            )}
            {catalogError && <p className="assistant-inline-error">{catalogError}</p>}
            {error && <p className="assistant-inline-error">{error}</p>}
            {!user && <div className="assistant-signin"><span>Sign in for image analysis and personalized product matches.</span><Link to="/login" onClick={() => onOpenChange(false)}>Sign in</Link></div>}
            <form className="assistant-composer" onSubmit={handleSubmit}>
              <input aria-label="Message the assistant" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={activeQuestion ? 'Or type your answer…' : 'Ask a skincare question…'} disabled={typing || busy} />
              <button type="submit" aria-label="Send message" disabled={!draft.trim() || typing || busy}><Send size={17} /></button>
            </form>
            <p className="assistant-disclaimer">General skin-care guidance only—not a medical diagnosis.</p>
          </div>
          <input ref={fileInput} className="assistant-file-input" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => void analyzePhoto(event.target.files?.[0])} />
        </section>
      )}
      <button className={`assistant-launcher ${open ? 'is-open' : ''}`} type="button" aria-label={open ? 'Close skincare assistant' : 'Open skincare assistant'} aria-expanded={open} onClick={() => onOpenChange(!open)}>
        {open ? <X size={22} /> : <MessageCircle size={23} />}
        {!open && <span>Ask AI</span>}
      </button>
    </div>
  )
}
