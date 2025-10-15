import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SearchBar from '@/components/SearchBar'

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    getSearchSuggestions: jest.fn(),
  },
}))

const mockApiClient = require('@/lib/api').apiClient

describe('SearchBar', () => {
  const mockOnSearch = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders search input', () => {
    render(<SearchBar onSearch={mockOnSearch} />)
    
    expect(screen.getByPlaceholderText(/suchen nach/i)).toBeInTheDocument()
  })

  it('calls onSearch when Enter is pressed', async () => {
    const user = userEvent.setup()
    render(<SearchBar onSearch={mockOnSearch} />)
    
    const input = screen.getByPlaceholderText(/suchen nach/i)
    await user.type(input, 'test query')
    await user.keyboard('{Enter}')
    
    expect(mockOnSearch).toHaveBeenCalledWith('test query')
  })

  it('shows suggestions when typing', async () => {
    const user = userEvent.setup()
    mockApiClient.getSearchSuggestions.mockResolvedValue({
      suggestions: ['BMW X5', 'BMW X3', 'Mercedes C-Class']
    })
    
    render(<SearchBar onSearch={mockOnSearch} />)
    
    const input = screen.getByPlaceholderText(/suchen nach/i)
    await user.type(input, 'BMW')
    
    await waitFor(() => {
      expect(screen.getByText('BMW X5')).toBeInTheDocument()
    })
  })

  it('handles keyboard navigation in suggestions', async () => {
    const user = userEvent.setup()
    mockApiClient.getSearchSuggestions.mockResolvedValue({
      suggestions: ['BMW X5', 'BMW X3']
    })
    
    render(<SearchBar onSearch={mockOnSearch} />)
    
    const input = screen.getByPlaceholderText(/suchen nach/i)
    await user.type(input, 'BMW')
    
    await waitFor(() => {
      expect(screen.getByText('BMW X5')).toBeInTheDocument()
    })
    
    // Arrow down to select first suggestion
    await user.keyboard('{ArrowDown}')
    
    // Enter should select the suggestion
    await user.keyboard('{Enter}')
    
    expect(mockOnSearch).toHaveBeenCalledWith('BMW X5')
  })

  it('closes suggestions when clicking outside', async () => {
    const user = userEvent.setup()
    mockApiClient.getSearchSuggestions.mockResolvedValue({
      suggestions: ['BMW X5']
    })
    
    render(<SearchBar onSearch={mockOnSearch} />)
    
    const input = screen.getByPlaceholderText(/suchen nach/i)
    await user.type(input, 'BMW')
    
    await waitFor(() => {
      expect(screen.getByText('BMW X5')).toBeInTheDocument()
    })
    
    // Click outside
    await user.click(document.body)
    
    await waitFor(() => {
      expect(screen.queryByText('BMW X5')).not.toBeInTheDocument()
    })
  })

  it('handles suggestion click', async () => {
    const user = userEvent.setup()
    mockApiClient.getSearchSuggestions.mockResolvedValue({
      suggestions: ['BMW X5']
    })
    
    render(<SearchBar onSearch={mockOnSearch} />)
    
    const input = screen.getByPlaceholderText(/suchen nach/i)
    await user.type(input, 'BMW')
    
    await waitFor(() => {
      expect(screen.getByText('BMW X5')).toBeInTheDocument()
    })
    
    // Click on suggestion
    await user.click(screen.getByText('BMW X5'))
    
    expect(mockOnSearch).toHaveBeenCalledWith('BMW X5')
  })

  it('shows loading indicator when fetching suggestions', async () => {
    const user = userEvent.setup()
    // Mock a slow response
    mockApiClient.getSearchSuggestions.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ suggestions: [] }), 100))
    )
    
    render(<SearchBar onSearch={mockOnSearch} />)
    
    const input = screen.getByPlaceholderText(/suchen nach/i)
    await user.type(input, 'BMW')
    
    // Should show loading indicator
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
