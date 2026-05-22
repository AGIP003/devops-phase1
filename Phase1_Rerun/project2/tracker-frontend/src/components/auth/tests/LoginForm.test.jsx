import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { expect, vi } from 'vitest'
import LoginForm from '../LoginForm'
import api from '../../../services/api'

vi.mock('../../../services/api', () => ({
  default: {
    post: vi.fn(),
  }
}))

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

function renderLogin() {
  return render(
    <MemoryRouter>
      <LoginForm />
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('LoginForm', () => {

  it('renders email and password fields and a submit button', () => {
    renderLogin()
    // YOUR CODE: assert that email input, password input, and submit button are present
    // Hint: use getByLabelText for inputs, getByRole for button/ 2. Find the email input by its placeholder text
    const emailInput = screen.getByPlaceholderText(/email/i)
    // 3. Assert it exists in the document
    expect(emailInput).toBeInTheDocument()

    // 4. Find the password input by placeholder
    const passwordInput = screen.getByPlaceholderText(/password/i)
    expect(passwordInput).toBeInTheDocument()

    // 5. Find the submit button by its role and name (text)
    const submitButton = screen.getByRole('button', { name: /login/i })
    expect(submitButton).toBeInTheDocument()
  })

  it('shows validation errors when submitted empty', async () => {
    const user = userEvent.setup()
    renderLogin()
    // YOUR CODE:
    // 1. Click the submit button without filling anything
    // 2. Assert that "Email is required" (or similar) text appears
    // Hint: React Hook Form shows errors after submit attempt
    const submitButton = screen.getByRole('button', { name: /login/i })
    await user.click(submitButton)

    //wait for the error message to appear
    const errorMessage = await screen.findByText(/email and password are required/i)
    expect(errorMessage).toBeInTheDocument()
  })

  it('calls api.post with correct credentials on valid submit', async () => {
    const user = userEvent.setup()
    // Tell the mock what to return on success
    api.post.mockResolvedValue({ data: { token: 'fake-jwt-token' } })

    renderLogin()
    screen.debug()
    // YOUR CODE:
    // 1. Type a valid email into the email field
    const emailInput = screen.getByPlaceholderText(/email/i)
    await user.type(emailInput, 'blessedmuchemi@gmail.com')
    // 2. Type a password into the password field
    const passwordInput = screen.getByPlaceholderText(/password/i)
    await user.type(passwordInput, 'Agip5118')
    // 3. Click the submit button
    const submitButton = screen.getByRole('button', { name: /login/i })
    await user.click(submitButton)
    // 4. Assert that api.post was called with '/auth/login' and the correct payload
    // Hint: expect(api.post).toHaveBeenCalledWith('/auth/login', { email: '...', password: '...' })
    expect(api.post).toHaveBeenCalledTimes(1)
    expect(api.post).toHaveBeenCalledWith('/auth/login', { email: 'blessedmuchemi@gmail.com', password: 'Agip5118' })
  })

  it('navigates to /dashboard after successful login', async () => {
    const user = userEvent.setup()
    api.post.mockResolvedValue({ data: { token: 'fake-jwt-token' } })

    renderLogin()
    // YOUR CODE:
    // 1. Fill and submit the form
    const emailInput = screen.getByPlaceholderText(/email/i)
    const passwordInput = screen.getByPlaceholderText(/password/i)
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'wrongpassword')
    const submitButton = screen.getByRole('button', { name: /login/i })
    await user.click(submitButton)
    // 2. Assert that mockNavigate was called with '/dashboard'
    
  })

  it('shows server error message on 401 response', async () => {
    const user = userEvent.setup()
    api.post.mockRejectedValue({
      response: { status: 401, data: { message: 'Invalid credentials' } }
    })

    renderLogin()
    // YOUR CODE:
    // 1. Fill and submit the form with any credentials
    const emailInput = screen.getByPlaceholderText(/email/i)
    const passwordInput = screen.getByPlaceholderText(/password/i)
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'wrongpassword')
    const submitButton = screen.getByRole('button', { name: /login/i })
    await user.click(submitButton)
    // 2. Assert that "Invalid credentials" text appears in the DOM
    // Hint: use findByText (async) because the error appears after the API call
    const errorMessage = await screen.findByText((content, element) =>
      content.toLowerCase().includes('invalid credentials')
    )
    expect(errorMessage).toBeInTheDocument()

  })

  it('disables the submit button while submitting', async () => {
    const user = userEvent.setup()
    // Make the API hang (never resolves) so we can check the loading state
    api.post.mockReturnValue(new Promise(() => { }))

    renderLogin()
    // YOUR CODE:
    // 1. Fill and submit the form
    const emailInput = screen.getByPlaceholderText(/email/i)
    const passwordInput = screen.getByPlaceholderText(/password/i)
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'wrongpassword')
    const submitButton = screen.getByRole('button', { name: /login/i })
    user.click(submitButton)
    // 2. Assert that the button is disabled (or shows loading text)
    // Hint: getByRole('button') + toBeDisabled()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /logging in/i })).toBeInTheDocument()})

  })

})