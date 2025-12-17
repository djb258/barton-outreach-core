export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "13.0.5"
  }
  public: {
    Tables: {
      company_monthly_updates: {
        Row: {
          approved: boolean | null
          created_at: string | null
          field_changed: string
          id: string
          new_value: string | null
          old_value: string | null
          source: string
          unique_id: string
          updated_at: string | null
        }
        Insert: {
          approved?: boolean | null
          created_at?: string | null
          field_changed: string
          id?: string
          new_value?: string | null
          old_value?: string | null
          source: string
          unique_id: string
          updated_at?: string | null
        }
        Update: {
          approved?: boolean | null
          created_at?: string | null
          field_changed?: string
          id?: string
          new_value?: string | null
          old_value?: string | null
          source?: string
          unique_id?: string
          updated_at?: string | null
        }
        Relationships: []
      }
      company_needs_enrichment: {
        Row: {
          company_name: string | null
          created_at: string | null
          hq_city: string | null
          industry: string | null
          linkedin_url: string | null
          state: string
          unique_id: string
          updated_at: string | null
          validated: boolean | null
          validation_source: string | null
          website: string | null
        }
        Insert: {
          company_name?: string | null
          created_at?: string | null
          hq_city?: string | null
          industry?: string | null
          linkedin_url?: string | null
          state: string
          unique_id?: string
          updated_at?: string | null
          validated?: boolean | null
          validation_source?: string | null
          website?: string | null
        }
        Update: {
          company_name?: string | null
          created_at?: string | null
          hq_city?: string | null
          industry?: string | null
          linkedin_url?: string | null
          state?: string
          unique_id?: string
          updated_at?: string | null
          validated?: boolean | null
          validation_source?: string | null
          website?: string | null
        }
        Relationships: []
      }
      edit_audit_log: {
        Row: {
          created_at: string
          field_name: string
          id: string
          new_value: string | null
          old_value: string | null
          record_id: string
          table_name: string
          user_id: string | null
        }
        Insert: {
          created_at?: string
          field_name: string
          id?: string
          new_value?: string | null
          old_value?: string | null
          record_id: string
          table_name: string
          user_id?: string | null
        }
        Update: {
          created_at?: string
          field_name?: string
          id?: string
          new_value?: string | null
          old_value?: string | null
          record_id?: string
          table_name?: string
          user_id?: string | null
        }
        Relationships: []
      }
      enrichment_log: {
        Row: {
          cost: number | null
          created_at: string | null
          entity: string
          id: string
          state: string
          success_count: number | null
          tool: string
          total_count: number | null
        }
        Insert: {
          cost?: number | null
          created_at?: string | null
          entity: string
          id?: string
          state: string
          success_count?: number | null
          tool: string
          total_count?: number | null
        }
        Update: {
          cost?: number | null
          created_at?: string | null
          entity?: string
          id?: string
          state?: string
          success_count?: number | null
          tool?: string
          total_count?: number | null
        }
        Relationships: []
      }
      monthly_update_log: {
        Row: {
          batch_size: number
          changes_found: number | null
          cost_usd: number | null
          created_at: string | null
          entity: string
          id: string
          promoted: number | null
          records_checked: number | null
          run_id: string
          runtime_sec: number | null
          state: string
          tool: string
        }
        Insert: {
          batch_size: number
          changes_found?: number | null
          cost_usd?: number | null
          created_at?: string | null
          entity: string
          id?: string
          promoted?: number | null
          records_checked?: number | null
          run_id?: string
          runtime_sec?: number | null
          state: string
          tool: string
        }
        Update: {
          batch_size?: number
          changes_found?: number | null
          cost_usd?: number | null
          created_at?: string | null
          entity?: string
          id?: string
          promoted?: number | null
          records_checked?: number | null
          run_id?: string
          runtime_sec?: number | null
          state?: string
          tool?: string
        }
        Relationships: []
      }
      n8n_call_log: {
        Row: {
          created_at: string | null
          error_message: string | null
          execution_time_ms: number
          id: string
          payload: Json
          response: Json | null
          status: string
          webhook_url: string
        }
        Insert: {
          created_at?: string | null
          error_message?: string | null
          execution_time_ms: number
          id?: string
          payload: Json
          response?: Json | null
          status: string
          webhook_url: string
        }
        Update: {
          created_at?: string | null
          error_message?: string | null
          execution_time_ms?: number
          id?: string
          payload?: Json
          response?: Json | null
          status?: string
          webhook_url?: string
        }
        Relationships: []
      }
      people_monthly_updates: {
        Row: {
          approved: boolean | null
          created_at: string | null
          field_changed: string
          id: string
          new_value: string | null
          old_value: string | null
          source: string
          unique_id: string
          updated_at: string | null
        }
        Insert: {
          approved?: boolean | null
          created_at?: string | null
          field_changed: string
          id?: string
          new_value?: string | null
          old_value?: string | null
          source: string
          unique_id: string
          updated_at?: string | null
        }
        Update: {
          approved?: boolean | null
          created_at?: string | null
          field_changed?: string
          id?: string
          new_value?: string | null
          old_value?: string | null
          source?: string
          unique_id?: string
          updated_at?: string | null
        }
        Relationships: []
      }
      people_needs_enrichment: {
        Row: {
          company_name: string | null
          created_at: string | null
          email: string | null
          first_name: string | null
          last_name: string | null
          linkedin_url: string | null
          state: string
          title: string | null
          unique_id: string
          updated_at: string | null
          validated: boolean | null
          validation_source: string | null
        }
        Insert: {
          company_name?: string | null
          created_at?: string | null
          email?: string | null
          first_name?: string | null
          last_name?: string | null
          linkedin_url?: string | null
          state: string
          title?: string | null
          unique_id?: string
          updated_at?: string | null
          validated?: boolean | null
          validation_source?: string | null
        }
        Update: {
          company_name?: string | null
          created_at?: string | null
          email?: string | null
          first_name?: string | null
          last_name?: string | null
          linkedin_url?: string | null
          state?: string
          title?: string | null
          unique_id?: string
          updated_at?: string | null
          validated?: boolean | null
          validation_source?: string | null
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
