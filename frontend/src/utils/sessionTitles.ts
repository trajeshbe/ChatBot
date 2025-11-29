/**
 * Shared utility for generating chat session titles
 * Used by both ChatHistory and SidebarModern components
 */

import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ChatSession {
  id: string
  session_id: string
  title: string | null
  created_at: string
  last_activity: string
  is_active: boolean
  message_count?: number
}

/**
 * Auto-generates titles for sessions that don't have one
 * Uses the backend endpoint which analyzes the conversation to create apt titles
 *
 * @param sessions - Array of chat sessions
 * @param token - Authentication token
 * @returns Sessions with auto-generated titles where applicable
 */
export async function generateMissingTitles(
  sessions: ChatSession[],
  token: string
): Promise<ChatSession[]> {
  const sessionsWithTitles = await Promise.all(
    sessions.map(async (session) => {
      // Only generate if session has no title but has messages
      if (!session.title && session.message_count && session.message_count > 0) {
        try {
          const titleResponse = await axios.patch(
            `${API_URL}/api/v1/sessions/${session.session_id}/title?auto_generate=true`,
            {},
            {
              headers: {
                Authorization: `Bearer ${token}`
              }
            }
          )

          if (titleResponse.data.title) {
            console.log(`✅ Auto-generated title for session ${session.session_id}: "${titleResponse.data.title}"`)
            return { ...session, title: titleResponse.data.title }
          }
        } catch (titleError) {
          console.warn(`Failed to generate title for session ${session.session_id}:`, titleError)
        }
      }
      return session
    })
  )

  return sessionsWithTitles
}
