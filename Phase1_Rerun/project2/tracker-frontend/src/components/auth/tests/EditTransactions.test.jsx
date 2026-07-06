import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { expect, vi } from 'vitest'
import EditTransaction from '../EditTransaction'
import api from '../../../services/api'

vi.mock('../../../services/api', () => ({
    default: { get: vi.fn(), put: vi.fn() 
    }
}))
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

// Fake transaction that your mock API will return
const fakeTransaction = {
  id: 1,
  description: 'Lunch at Java',
  amount: 850,
  type: 'expense',
  category: 'food',
  date: '2026-05-14',
  payment_method: 'cash',
}

// Renders EditTransaction at /transactions/edit/1 so useParams gets id='1'
function renderEdit() {
  return render(
    <MemoryRouter initialEntries={['/transactions/edit/1']}>
      <Routes>
        <Route path="/transactions/edit/:id" element={<EditTransaction />} />
      </Routes>
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('EditTransaction', () => {

  it('pre-fills form with existing transaction data', async () => {
    api.get.mockResolvedValue({ data: fakeTransaction })
    renderEdit()

    // Wait for the API data to be loaded into the form.
    const descriptionInput = await screen.findByDisplayValue(fakeTransaction.description)
    expect(descriptionInput).toBeInTheDocument()

    // Number inputs store display values as strings in the DOM.
    const amountInput = await screen.findByDisplayValue(String(fakeTransaction.amount))
    expect(amountInput).toBeInTheDocument()

    // Check select fields by their selected display value and submitted value.
    const typeSelect = screen.getByDisplayValue('Expense')
    expect(typeSelect).toHaveValue(fakeTransaction.type)

    const categorySelect = screen.getByDisplayValue(fakeTransaction.category)
    expect(categorySelect).toHaveValue(fakeTransaction.category)

    const dateInput = screen.getByDisplayValue(fakeTransaction.date)
    expect(dateInput).toBeInTheDocument()

    const paymentMethodSelect = screen.getByDisplayValue(fakeTransaction.payment_method)
    expect(paymentMethodSelect).toHaveValue(fakeTransaction.payment_method)
  })

  it('Save button is disabled until user changes a field', async () => {
    const user = userEvent.setup()
    api.get.mockResolvedValue({ data: fakeTransaction })
    renderEdit()

    // reset(data) should pre-fill the form and keep isDirty false.
    const descriptionInput = await screen.findByDisplayValue(fakeTransaction.description)
    expect(descriptionInput).toBeInTheDocument()

    const amountInput = await screen.findByDisplayValue(String(fakeTransaction.amount))
    expect(amountInput).toBeInTheDocument()

    const saveButton = screen.getByRole('button', { name: /save changes/i })
    expect(saveButton).toBeDisabled()

    // Editing a field should mark the form dirty and enable saving.
    await user.clear(descriptionInput)
    await user.type(descriptionInput, 'Dinner at Java')

    expect(saveButton).toBeEnabled()
  })

  it('sends PUT request with updated data on save', async () => {
    const user = userEvent.setup()
    api.get.mockResolvedValue({ data: fakeTransaction })
    api.put.mockResolvedValue({ data: { ...fakeTransaction, description: 'Dinner at Java' } })
    
    renderEdit()

    // Change a field after the existing transaction is loaded.
    const descriptionInput = await screen.findByDisplayValue(fakeTransaction.description)
    await user.clear(descriptionInput)
    await user.type(descriptionInput, 'Dinner at Java')

    await user.click(screen.getByRole('button', { name: /save changes/i }))

    // The component should submit the updated data to the transaction endpoint.
    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith('/transactions/1', {
        ...fakeTransaction,
        description: 'Dinner at Java',
      })
    })
    expect(mockNavigate).toHaveBeenCalledWith('/transactions')
  })

  it('shows error if fetch fails', async () => {
    api.get.mockRejectedValue({ response: { data: { message: 'Not found' } } })
    renderEdit()

    // Fetch errors should be shown to the user.
    expect(await screen.findByText(/failed to load transaction/i)).toBeInTheDocument()
  })

})
