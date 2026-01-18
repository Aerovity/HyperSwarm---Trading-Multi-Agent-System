import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Map backend USDC pairs to frontend trading pair display format
export function mapPairToDisplayFormat(backendPair: string): string {
  const pairMapping: Record<string, string> = {
    'BTC/USDC': 'BTC/ETH',
    'ETH/USDC': 'ETH/SOL',
    'SOL/USDC': 'SOL/BTC',
    'ARB/USDC': 'ARB/ETH',
    'AVAX/USDC': 'SOL/ETH', // AVAX maps to SOL/ETH as 5th pair
  }

  return pairMapping[backendPair] || backendPair
}

// Reverse map: Convert display format back to backend format
export function mapDisplayToBackendFormat(displayPair: string): string {
  const reverseMapping: Record<string, string> = {
    'BTC/ETH': 'BTC/USDC',
    'ETH/SOL': 'ETH/USDC',
    'SOL/BTC': 'SOL/USDC',
    'ARB/ETH': 'ARB/USDC',
    'SOL/ETH': 'AVAX/USDC',
  }

  return reverseMapping[displayPair] || displayPair
}
